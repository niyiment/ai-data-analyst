"""Gemini adapter implementing the LLMClient port (ADR-0007)."""

import asyncio
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.errors import QuotaExceeded

T = TypeVar("T", bound=BaseModel)


class GeminiLLMClient:
    """Calls Gemini with structured JSON output and validates against a Pydantic model."""

    def __init__(self, *, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """Invoke Gemini in a worker thread and validate the JSON response."""
        return await asyncio.to_thread(
            self._call_sync,
            system_prompt,
            user_prompt,
            response_model,
        )

    def _call_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=response_model,
                    temperature=0.0,
                ),
            )
        except Exception as exc:
            if "429" in str(exc) or "quota" in str(exc).lower():
                raise QuotaExceeded("LLM quota exceeded. Please try again shortly.") from exc
            raise

        text = response.text or "{}"
        return response_model.model_validate_json(text)
