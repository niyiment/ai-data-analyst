"""Unit tests for LLM factory, Ollama adapter, and Claude adapter (ADR-0007)."""

import httpx
import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import QuotaExceeded, ValidationRejected
from app.llm.claude import ClaudeLLMClient
from app.llm.factory import build_llm_client
from app.llm.gemini import GeminiLLMClient
from app.llm.ollama import OllamaLLMClient


class SampleAnswer(BaseModel):
    sql: str
    confidence: float


def test_factory_builds_ollama_by_default() -> None:
    settings = Settings()
    client = build_llm_client(settings=settings)
    assert isinstance(client, OllamaLLMClient)


def test_factory_builds_ollama_cloud_with_api_key() -> None:
    settings = Settings()
    client = build_llm_client(
        settings=settings, provider="ollama_cloud", api_key="ollama-cloud-key"
    )
    assert isinstance(client, OllamaLLMClient)


def test_factory_builds_gemini_when_requested() -> None:
    settings = Settings(gemini_api_key="test-gemini-key")
    client = build_llm_client(settings=settings, provider="gemini")
    assert isinstance(client, GeminiLLMClient)


def test_factory_builds_claude_when_requested() -> None:
    settings = Settings(anthropic_api_key="test-claude-key")
    client = build_llm_client(settings=settings, provider="claude", api_key="user-claude-key")
    assert isinstance(client, ClaudeLLMClient)


def test_factory_rejects_unknown_provider() -> None:
    settings = Settings()
    with pytest.raises(ValidationRejected):
        build_llm_client(settings=settings, provider="unknown-llm")


@pytest.mark.asyncio
async def test_ollama_client_parses_structured_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": '{"sql":"SELECT 1","confidence":1}'}},
        )

    client = OllamaLLMClient(transport=httpx.MockTransport(handler))
    result = await client.generate_structured(
        system_prompt="You are a SQL assistant.",
        user_prompt="Count rows",
        response_model=SampleAnswer,
    )
    assert result.sql == "SELECT 1"
    assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_ollama_cloud_sends_bearer_token_and_maps_429() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer ollama-cloud-key"
        return httpx.Response(429, json={"error": "rate_limit"})

    client = OllamaLLMClient(
        base_url="https://ollama.com",
        api_key="ollama-cloud-key",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(QuotaExceeded):
        await client.generate_structured(
            system_prompt="sys",
            user_prompt="usr",
            response_model=SampleAnswer,
        )


@pytest.mark.asyncio
async def test_claude_client_parses_structured_json() -> None:
    fenced = '```json\n{"sql": "SELECT 1", "confidence": 0.95}\n```'

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "sk-ant-test"
        return httpx.Response(
            200,
            json={"content": [{"type": "text", "text": fenced}]},
        )

    transport = httpx.MockTransport(handler)
    client = ClaudeLLMClient(api_key="sk-ant-test", transport=transport)
    result = await client.generate_structured(
        system_prompt="You are a SQL assistant.",
        user_prompt="Count rows",
        response_model=SampleAnswer,
    )
    assert result.sql == "SELECT 1"
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_claude_client_maps_429_to_quota_exceeded() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(429, json={"error": "rate_limit"}))
    client = ClaudeLLMClient(api_key="sk-ant-test", transport=transport)
    with pytest.raises(QuotaExceeded):
        await client.generate_structured(
            system_prompt="sys",
            user_prompt="usr",
            response_model=SampleAnswer,
        )
