"""Sliding-window rate limiter and global quota guard (US-15)."""

from collections import defaultdict, deque
from collections.abc import Callable
from math import ceil
from time import monotonic

from app.core.errors import QuotaExceeded, RateLimited


class RateLimiter:
    """In-memory sliding-window rate limiter keyed by session or IP."""

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        """Record a hit for key or raise RateLimited with retry_after_seconds."""
        now = self._clock()
        bucket = self._hits[key]
        cutoff = now - self._window
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= self._limit:
            retry_after = max(1, ceil(self._window - (now - bucket[0])))
            raise RateLimited(
                f"Rate limit exceeded. Retry in {retry_after} seconds.",
                details={"retry_after_seconds": retry_after},
            )
        bucket.append(now)


class QuotaGuard:
    """Global sliding-window budget guard for LLM calls."""

    def __init__(
        self,
        max_calls: int,
        window_seconds: int = 86400,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._clock = clock
        self._calls: deque[float] = deque()

    def consume(self) -> None:
        """Consume one LLM call from the global budget or raise QuotaExceeded."""
        now = self._clock()
        cutoff = now - self._window
        while self._calls and self._calls[0] <= cutoff:
            self._calls.popleft()

        if len(self._calls) >= self._max_calls:
            retry_after = max(1, ceil(self._window - (now - self._calls[0])))
            raise QuotaExceeded(
                f"Global LLM quota exceeded. Retry in {retry_after} seconds.",
                details={"retry_after_seconds": retry_after},
            )
        self._calls.append(now)
