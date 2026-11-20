"""End-to-end API flows over real PostgreSQL; only the LLM is faked.

Exercises routers, services, SQL repositories, per-dataset DDL, the AST validator,
and the analyst_ro executor together.
"""

from collections.abc import AsyncIterator
from typing import TypeVar

import psycopg
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.database import get_db_session
from app.insights.schemas import InsightsPayload
from app.llm.factory import get_llm_client
from app.main import create_app
from app.query.schemas import QueryPlan, SqlGenerationOutput

T = TypeVar("T", bound=BaseModel)
OWNER_DSN = "postgresql://app_owner:local_owner_password@localhost:5433/ai_data_analyst"
CLEANUP_SECRET = "integration-cleanup-secret"


class ScriptedLLM:
    """Answers each structured call by response model; SQL is set per test."""

    def __init__(self) -> None:
        self.sql = "SELECT region, SUM(revenue) AS total FROM retail_sales GROUP BY region"

    async def generate_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> T:
        if response_model is QueryPlan:
            return response_model.model_validate({"intent": "aggregate", "tables": []})
        if response_model is SqlGenerationOutput:
            return response_model.model_validate({"sql": self.sql})
        if response_model is InsightsPayload:
            return response_model.model_validate(
                {"summary": "North leads.", "key_findings": ["North is highest"]}
            )
        raise AssertionError(f"unexpected model {response_model}")


def _ds_schema_count() -> int:
    with psycopg.connect(OWNER_DSN) as conn:
        row = conn.execute(
            "SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'ds\\_%'"
        ).fetchone()
        return int(row[0]) if row else 0


def _app(engine: AsyncEngine, llm: ScriptedLLM) -> FastAPI:
    settings = get_settings().model_copy(update={"cleanup_secret": CLEANUP_SECRET})
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def db() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = db
    app.dependency_overrides[get_llm_client] = lambda: llm
    app.dependency_overrides[get_settings] = lambda: settings
    return app


@pytest.fixture
def llm() -> ScriptedLLM:
    return ScriptedLLM()


@pytest.fixture
async def app(llm: ScriptedLLM) -> AsyncIterator[FastAPI]:
    engine = create_async_engine(get_settings().database_url_app)
    yield _app(engine, llm)
    await engine.dispose()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as http:
        yield http


async def _new_session(http: AsyncClient) -> None:
    assert (await http.post("/api/v1/sessions")).status_code == 201


async def _load_sample(http: AsyncClient) -> dict[str, object]:
    resp = await http.post("/api/v1/datasets/samples/retail_sales")
    assert resp.status_code == 201, resp.text
    body: dict[str, object] = resp.json()
    return body


async def test_full_analysis_flow_from_sample_to_exported_report(client: AsyncClient) -> None:
    await _new_session(client)
    ds_id = (await _load_sample(client))["id"]

    listed = (await client.get("/api/v1/datasets")).json()
    assert [d["id"] for d in listed["items"]] == [ds_id]

    asked = await client.post(f"/api/v1/datasets/{ds_id}/queries", json={"question": "Revenue?"})
    answer = asked.json()
    assert answer["status"] == "succeeded", answer
    assert {r["region"] for r in answer["rows"]} >= {"North", "South"}
    assert answer["chart_spec"]["x"] == "region"

    history = (await client.get(f"/api/v1/datasets/{ds_id}/queries")).json()
    assert history["total"] == 1

    insights = await client.post(f"/api/v1/queries/{answer['id']}/insights")
    assert insights.json()["summary"] == "North leads."

    report = await client.post(
        "/api/v1/reports", json={"title": "Q1", "items": [{"query_run_id": answer["id"]}]}
    )
    assert report.status_code == 201
    report_id = report.json()["id"]

    html = await client.get(f"/api/v1/reports/{report_id}/export?format=html")
    assert html.status_code == 200 and "Revenue?" in html.text
    pdf = await client.get(f"/api/v1/reports/{report_id}/export?format=pdf")
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF")


async def test_column_rename_is_persisted(client: AsyncClient) -> None:
    await _new_session(client)
    dataset = await _load_sample(client)
    column = dataset["tables"][0]["columns"][1]  # type: ignore[index]

    patched = await client.patch(
        f"/api/v1/datasets/{dataset['id']}/columns/{column['id']}",
        json={"column_name": "order_day"},
    )

    assert patched.status_code == 200, patched.text
    detail = (await client.get(f"/api/v1/datasets/{dataset['id']}")).json()
    assert "order_day" in [c["column_name"] for c in detail["tables"][0]["columns"]]


async def test_csv_upload_creates_and_delete_drops_an_isolated_schema(client: AsyncClient) -> None:
    await _new_session(client)
    before = _ds_schema_count()
    csv = b"City,Sales\nLagos,10\nAccra,7\n=SUM(1),3\n"

    uploaded = await client.post(
        "/api/v1/datasets", files={"file": ("cities.csv", csv, "text/csv")}
    )

    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["tables"][0]["row_count"] == 3
    assert _ds_schema_count() == before + 1
    deleted = await client.delete(f"/api/v1/datasets/{uploaded.json()['id']}")
    assert deleted.status_code == 204
    assert _ds_schema_count() == before


async def test_unsafe_model_sql_is_rejected_and_data_survives(
    client: AsyncClient, llm: ScriptedLLM
) -> None:
    await _new_session(client)
    ds_id = (await _load_sample(client))["id"]
    llm.sql = "DELETE FROM retail_sales"
    url = f"/api/v1/datasets/{ds_id}/queries"

    rejected = (await client.post(url, json={"question": "Wipe it"})).json()
    llm.sql = "SELECT COUNT(*) AS n FROM retail_sales"
    counted = (await client.post(url, json={"question": "Count rows"})).json()

    assert rejected["status"] == "rejected"
    assert counted["rows"][0]["n"] > 0


async def test_sessions_cannot_see_each_others_datasets(app: FastAPI) -> None:
    async with (
        AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as alice,
        AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as bob,
    ):
        await _new_session(alice)
        await _new_session(bob)
        ds_id = (await _load_sample(alice))["id"]

        assert (await bob.get(f"/api/v1/datasets/{ds_id}")).status_code == 404
        asked = await bob.post(f"/api/v1/datasets/{ds_id}/queries", json={"question": "hi?"})
        assert asked.status_code == 404
        assert (await bob.get("/api/v1/datasets")).json()["items"] == []


async def test_delete_my_data_drops_schemas_and_ends_the_session(client: AsyncClient) -> None:
    await _new_session(client)
    await _load_sample(client)
    before = _ds_schema_count()

    deleted = await client.delete("/api/v1/sessions/me")

    assert deleted.status_code == 200
    assert deleted.json()["schemas_dropped"] == 1
    assert _ds_schema_count() == before - 1
    assert (await client.get("/api/v1/sessions/me")).status_code == 401


async def test_cleanup_requires_the_secret_and_purges_expired_sessions(
    client: AsyncClient,
) -> None:
    await _new_session(client)
    await _load_sample(client)
    session_id = (await client.get("/api/v1/sessions/me")).json()["session_id"]
    with psycopg.connect(OWNER_DSN) as conn:
        conn.execute(
            "UPDATE app.sessions SET expires_at = now() - interval '1 hour' WHERE id = %s",
            (session_id,),
        )

    forbidden = await client.post("/api/v1/internal/cleanup", headers={"X-Cleanup-Secret": "no"})
    allowed = await client.post(
        "/api/v1/internal/cleanup", headers={"X-Cleanup-Secret": CLEANUP_SECRET}
    )

    assert forbidden.status_code in (401, 403)
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["sessions_deleted"] >= 1
    assert allowed.json()["schemas_dropped"] >= 1
