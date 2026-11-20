"""API tests for /api/v1/eval endpoints (US-14 & US-15)."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_eval_sets_and_run_lifecycle() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sets_resp = await client.get("/api/v1/eval/sets")
        assert sets_resp.status_code == 200
        sets = sets_resp.json()
        assert any(s["name"] == "retail_sales" for s in sets)

        run_resp = await client.post("/api/v1/eval/runs", json={"set_name": "retail_sales"})
        assert run_resp.status_code == 201
        run = run_resp.json()
        assert run["set_name"] == "retail_sales"
        assert run["accuracy"] == 1.0
        assert run["rejection_rate"] == 0.0

        get_resp = await client.get(f"/api/v1/eval/runs/{run['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == run["id"]


@pytest.mark.asyncio
async def test_eval_run_not_found_returns_standard_error() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/eval/runs/{uuid4()}")
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "NOT_FOUND"
        assert "request_id" in body
