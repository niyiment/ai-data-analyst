"""Anthropic Claude adapter implementing the LLMClient port (ADR-0007)."""

import json
import re
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.core.errors import QuotaExceeded
from app.llm.http import post_json
from app.llm.usage import record_usage

T = TypeVar("T", bound=BaseModel)

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip()).strip()


class ClaudeLLMClient:
    """Calls Anthropic Messages API and validates JSON output against a Pydantic model."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-3-5-sonnet-latest",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._transport = transport

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """Invoke Claude and validate the returned JSON against response_model."""
        response = await post_json(
            _ANTHROPIC_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": _ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            payload=self._payload(system_prompt, user_prompt, response_model),
            timeout=30.0,
            transport=self._transport,
        )
        if response.status_code == 429:
            raise QuotaExceeded("LLM quota exceeded. Please try again shortly.")
        response.raise_for_status()

        body = response.json()
        usage = body.get("usage", {})
        record_usage(usage.get("input_tokens"), usage.get("output_tokens"))
        blocks = body.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return response_model.model_validate_json(_strip_fences(text) or "{}")

    def _payload(
        self, system_prompt: str, user_prompt: str, response_model: type[BaseModel]
    ) -> dict[str, object]:
        schema_json = json.dumps(response_model.model_json_schema())
        system = (
            f"{system_prompt}\n\n"
            f"Respond ONLY with valid JSON matching this JSON schema:\n{schema_json}"
        )
        return {
            "model": self._model,
            "max_tokens": 2048,
            "temperature": 0.0,
            "system": system,
            "messages": [{"role": "user", "content": user_prompt}],
        }
