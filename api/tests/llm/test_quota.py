"""Unit tests for the quota-guarded LLM client decorator (US-15)."""

from typing import TypeVar

import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import QuotaExceeded
from app.core.rate_limit import QuotaGuard
from app.llm.factory import get_llm_client
from app.llm.quota import QuotaGuardedLLMClient

T = TypeVar("T", bound=BaseModel)


class Answer(BaseModel):
    text: str


class RecordingClient:
    """Fake LLMClient that counts calls."""

    def __init__(self) -> None:
        self.calls = 0

    async def generate_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> T:
        self.calls += 1
        return response_model.model_validate({"text": "ok"})


async def _ask(client: QuotaGuardedLLMClient) -> Answer:
    return await client.generate_structured(
        system_prompt="s", user_prompt="u", response_model=Answer
    )


@pytest.mark.asyncio
async def test_guarded_client_delegates_while_budget_remains() -> None:
    inner = RecordingClient()
    client = QuotaGuardedLLMClient(inner, QuotaGuard(max_calls=2))

    result = await _ask(client)

    assert result.text == "ok"
    assert inner.calls == 1


@pytest.mark.asyncio
async def test_guarded_client_raises_without_calling_model_when_exhausted() -> None:
    inner = RecordingClient()
    client = QuotaGuardedLLMClient(inner, QuotaGuard(max_calls=1))
    await _ask(client)

    with pytest.raises(QuotaExceeded) as exc_info:
        await _ask(client)

    assert inner.calls == 1
    assert exc_info.value.details is not None
    assert exc_info.value.details["retry_after_seconds"] > 0


def test_request_dependency_returns_quota_guarded_client() -> None:
    client = get_llm_client(Settings())

    assert isinstance(client, QuotaGuardedLLMClient)
