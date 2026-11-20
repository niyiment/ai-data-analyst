"""LLM adapters reuse one HTTP client per event loop.

Building an httpx.AsyncClient does synchronous TLS/CA setup (~300 ms measured on
Windows). Doing it per call blocked the event loop; the load test showed p95 13 s.
"""

import httpx
import pytest
from pydantic import BaseModel

from app.llm import http as llm_http
from app.llm.claude import ClaudeLLMClient
from app.llm.ollama import OllamaLLMClient


class Answer(BaseModel):
    sql: str


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/chat":
        return httpx.Response(200, json={"message": {"content": '{"sql": "SELECT 1"}'}})
    return httpx.Response(200, json={"content": [{"type": "text", "text": '{"sql": "SELECT 1"}'}]})


@pytest.fixture
def constructed(monkeypatch: pytest.MonkeyPatch) -> list[httpx.AsyncClient]:
    """Count real client constructions; route all traffic to a mock transport."""
    made: list[httpx.AsyncClient] = []
    real = httpx.AsyncClient

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        client = real(transport=httpx.MockTransport(_handler))
        made.append(client)
        return client

    monkeypatch.setattr(llm_http.httpx, "AsyncClient", factory)
    llm_http.reset_shared_clients()
    return made


async def _ask(client: OllamaLLMClient | ClaudeLLMClient) -> Answer:
    return await client.generate_structured(system_prompt="s", user_prompt="u", response_model=Answer)


async def test_shared_client_is_reused_within_an_event_loop(
    constructed: list[httpx.AsyncClient],
) -> None:
    assert llm_http.shared_async_client() is llm_http.shared_async_client()
    assert len(constructed) == 1


async def test_adapters_do_not_build_a_client_per_call(
    constructed: list[httpx.AsyncClient],
) -> None:
    for _ in range(3):
        assert (await _ask(OllamaLLMClient())).sql == "SELECT 1"
        assert (await _ask(ClaudeLLMClient(api_key="k"))).sql == "SELECT 1"

    assert len(constructed) == 1
