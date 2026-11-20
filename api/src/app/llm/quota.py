"""Global LLM quota guard applied to every model call (US-15)."""

from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.rate_limit import QuotaGuard
from app.llm.port import LLMClient

T = TypeVar("T", bound=BaseModel)

_DAY_SECONDS = 86400


class QuotaGuardedLLMClient:
    """LLMClient decorator that spends one unit of the global budget per call."""

    def __init__(self, inner: LLMClient, guard: QuotaGuard) -> None:
        self._inner = inner
        self._guard = guard

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """Consume budget, then delegate; raises QuotaExceeded before calling the model."""
        self._guard.consume()
        return await self._inner.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
        )


@lru_cache(maxsize=1)
def get_quota_guard() -> QuotaGuard:
    """Return the process-wide daily LLM call budget."""
    return QuotaGuard(
        max_calls=get_settings().llm_daily_call_budget, window_seconds=_DAY_SECONDS
    )
