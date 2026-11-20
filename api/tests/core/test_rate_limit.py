"""Unit tests for sliding-window rate limiter and global quota guard (US-15)."""

import pytest

from app.core.errors import QuotaExceeded, RateLimited
from app.core.rate_limit import QuotaGuard, RateLimiter


class FakeClock:
    """Deterministic clock for testing time-window expiry."""

    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_rate_limiter_allows_up_to_limit() -> None:
    clock = FakeClock()
    limiter = RateLimiter(limit=2, window_seconds=60, clock=clock)

    limiter.check("session-a")
    limiter.check("session-a")


def test_rate_limiter_blocks_over_limit_with_retry_after() -> None:
    clock = FakeClock()
    limiter = RateLimiter(limit=2, window_seconds=60, clock=clock)

    limiter.check("session-a")
    clock.advance(10)
    limiter.check("session-a")

    with pytest.raises(RateLimited) as exc_info:
        limiter.check("session-a")

    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "RATE_LIMITED"
    assert exc_info.value.details is not None
    assert exc_info.value.details["retry_after_seconds"] == 50


def test_rate_limiter_isolates_keys_and_resets_after_window() -> None:
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window_seconds=30, clock=clock)

    limiter.check("session-a")
    limiter.check("session-b")

    clock.advance(31)
    limiter.check("session-a")


def test_quota_guard_raises_when_daily_budget_exhausted() -> None:
    clock = FakeClock()
    guard = QuotaGuard(max_calls=2, window_seconds=3600, clock=clock)

    guard.consume()
    guard.consume()

    with pytest.raises(QuotaExceeded) as exc_info:
        guard.consume()

    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "QUOTA_EXCEEDED"
    assert exc_info.value.details is not None
    assert exc_info.value.details["retry_after_seconds"] > 0
