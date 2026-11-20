"""Factory and FastAPI dependency for selecting Ollama (local/cloud), Gemini, or Claude."""

from typing import Annotated

from fastapi import Depends, Header

from app.core.config import Settings, get_settings
from app.core.errors import ValidationRejected
from app.llm.claude import ClaudeLLMClient
from app.llm.gemini import GeminiLLMClient
from app.llm.ollama import OllamaLLMClient
from app.llm.port import LLMClient
from app.llm.quota import QuotaGuardedLLMClient, get_quota_guard


def build_llm_client(
    *,
    settings: Settings,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> LLMClient:
    """Instantiate Ollama (local or cloud), Gemini, or Claude client."""
    chosen = (provider or settings.llm_provider or "ollama").strip().lower()
    if chosen == "ollama":
        return OllamaLLMClient(
            base_url=settings.ollama_base_url,
            model=(model or settings.ollama_model).strip(),
        )
    if chosen == "ollama_cloud":
        return OllamaLLMClient(
            base_url=settings.ollama_cloud_base_url,
            model=(model or settings.ollama_cloud_model).strip(),
            api_key=(api_key or settings.ollama_cloud_api_key).strip(),
        )
    if chosen == "gemini":
        return GeminiLLMClient(
            api_key=(api_key or settings.gemini_api_key).strip(),
            model=(model or settings.gemini_model).strip(),
        )
    if chosen == "claude":
        return ClaudeLLMClient(
            api_key=(api_key or settings.anthropic_api_key).strip(),
            model=(model or settings.claude_model).strip(),
        )
    raise ValidationRejected(
        f"Unsupported LLM provider '{chosen}'. "
        "Use 'ollama', 'ollama_cloud', 'gemini', or 'claude'."
    )


def describe_llm(
    settings: Settings, provider: str | None = None, model: str | None = None
) -> str:
    """Return a 'provider:model' label for reporting which model produced a result."""
    chosen = (provider or settings.llm_provider or "ollama").strip().lower()
    defaults = {
        "ollama": settings.ollama_model,
        "ollama_cloud": settings.ollama_cloud_model,
        "gemini": settings.gemini_model,
        "claude": settings.claude_model,
    }
    return f"{chosen}:{(model or defaults.get(chosen, 'unknown')).strip()}"


def get_llm_client(
    settings: Annotated[Settings, Depends(get_settings)],
    x_llm_provider: Annotated[str | None, Header()] = None,
    x_llm_api_key: Annotated[str | None, Header()] = None,
    x_llm_model: Annotated[str | None, Header()] = None,
) -> LLMClient:
    """Resolve the quota-guarded LLMClient for the current request."""
    client = build_llm_client(
        settings=settings,
        provider=x_llm_provider,
        api_key=x_llm_api_key,
        model=x_llm_model,
    )
    return QuotaGuardedLLMClient(client, get_quota_guard())
