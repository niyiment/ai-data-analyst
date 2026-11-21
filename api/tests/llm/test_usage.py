"""Token usage is recorded per call and measured per scope (US-14 token cost metric)."""

from types import SimpleNamespace
from typing import Any

import httpx
from pydantic import BaseModel

from app.llm.claude import ClaudeLLMClient
from app.llm.gemini import GeminiLLMClient
from app.llm.ollama import OllamaLLMClient
from app.llm.usage import measure_usage, record_usage


class Answer(BaseModel):
    sql: str


async def _ask(client: Any) -> Answer:
    result: Answer = await client.generate_structured(
        system_prompt="s", user_prompt="u", response_model=Answer
    )
    return result


def test_recording_outside_a_measurement_is_a_no_op() -> None:
    record_usage(10, 5)

    with measure_usage() as meter:
        record_usage(3, 2)
        record_usage(4, 1)

    assert (meter.tokens_in, meter.tokens_out) == (7, 3)


async def test_ollama_records_prompt_and_eval_counts() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        body = {"message": {"content": '{"sql": "SELECT 1"}'}, "prompt_eval_count": 120}
        return httpx.Response(200, json={**body, "eval_count": 30})

    with measure_usage() as meter:
        await _ask(OllamaLLMClient(transport=httpx.MockTransport(handler)))

    assert (meter.tokens_in, meter.tokens_out) == (120, 30)


async def test_claude_records_input_and_output_tokens() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": '{"sql": "SELECT 1"}'}],
                "usage": {"input_tokens": 200, "output_tokens": 40},
            },
        )

    client = ClaudeLLMClient(api_key="k", transport=httpx.MockTransport(handler))
    with measure_usage() as meter:
        await _ask(client)

    assert (meter.tokens_in, meter.tokens_out) == (200, 40)


async def test_gemini_records_usage_metadata() -> None:
    client = GeminiLLMClient(api_key="k")
    response = SimpleNamespace(
        text='{"sql": "SELECT 1"}',
        usage_metadata=SimpleNamespace(prompt_token_count=90, candidates_token_count=12),
    )
    fake_models = SimpleNamespace(generate_content=lambda **_: response)
    client._client = SimpleNamespace(models=fake_models)  # type: ignore[assignment]

    with measure_usage() as meter:
        await _ask(client)

    assert (meter.tokens_in, meter.tokens_out) == (90, 12)
