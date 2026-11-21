# ADR-0013: Multi-provider LLM selection behind the port

- **Status:** Proposed
- **Date:** 2026-11-20

## Context

ADR-0007 put every model call behind an `LLMClient` port, with Gemini as the only adapter. In practice, Gemini's free-tier quota is small for development and evaluation runs (a full golden-set run is about 60 calls). Contributors also want to run the app without any API key. Some users want to compare models, or bring their own key for a stronger model.

## Decision

- Provide four adapters behind the same port: `ollama` (local, no key, the default), `ollama_cloud`, `gemini`, and `claude`. `app/llm/factory.py` builds them.
- Choose the default with `LLM_PROVIDER` and per-provider settings. A request may override the provider, model, and API key with the `X-LLM-Provider`, `X-LLM-Model`, and `X-LLM-Api-Key` headers, which the web Settings page sends.
- Wrap every client in `QuotaGuardedLLMClient`, which applies the global daily budget (`LLM_DAILY_CALL_BUDGET`) whichever provider is used.
- Adapters report provider token usage through the context-scoped meter in `app/llm/usage.py`. This keeps the port's signature unchanged.
- Label evaluation runs `provider:model` so results from different models stay comparable.

## Consequences

- Development and evaluation work offline at no cost with Ollama. Accuracy numbers depend on the model, so every run records its label.
- User-supplied keys travel in request headers. They must never be logged, stored, or placed in URLs (`docs/SECURITY.md`). The same-origin proxy (ADR-0010) keeps them first-party.
- Every adapter must return output validated against the requested Pydantic model and map rate limits to `QUOTA_EXCEEDED`. A new provider means a new adapter plus tests, with no service changes.
- Prompts are versioned per pipeline, not per provider. If a model needs different prompts, that needs a new decision.
