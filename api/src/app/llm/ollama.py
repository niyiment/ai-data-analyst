"""Ollama local and cloud adapter implementing the LLMClient port (ADR-0007)."""

import re
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.core.errors import QuotaExceeded
from app.llm.usage import record_usage

T = TypeVar("T", bound=BaseModel)

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip()).strip()


class OllamaLLMClient:
    """Calls a local or cloud Ollama endpoint with structured JSON schema output."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        api_key: str = "",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key.strip()
        self._transport = transport

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """Invoke Ollama /api/chat and validate the JSON response against response_model."""
        headers: dict[str, str] = {"content-type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "stream": False,
            "format": response_model.model_json_schema(),
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        async with httpx.AsyncClient(transport=self._transport, timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat", headers=headers, json=payload
            )

        if response.status_code == 429:
            raise QuotaExceeded("LLM quota exceeded. Please try again shortly.")
        response.raise_for_status()
        body = response.json()
        record_usage(body.get("prompt_eval_count"), body.get("eval_count"))
        content = body.get("message", {}).get("content", "{}")
        return response_model.model_validate_json(_strip_fences(content) or "{}")
