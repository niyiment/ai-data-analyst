"""Context-scoped token usage metering for LLM calls (US-14 token cost metric).

Adapters call record_usage after each provider response. Callers that need totals
(for example, the evaluation runner) wrap work in measure_usage(). Recording outside
a measurement is a no-op, so the LLMClient port signature stays unchanged.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class UsageMeter:
    """Running token totals for one measurement scope."""

    tokens_in: int = 0
    tokens_out: int = 0


_current: ContextVar[UsageMeter | None] = ContextVar("llm_usage_meter", default=None)


def record_usage(tokens_in: int | None, tokens_out: int | None) -> None:
    """Add provider-reported token counts to the active meter, if any."""
    meter = _current.get()
    if meter is not None:
        meter.tokens_in += tokens_in or 0
        meter.tokens_out += tokens_out or 0


@contextmanager
def measure_usage() -> Iterator[UsageMeter]:
    """Collect token usage from LLM calls made inside the block."""
    meter = UsageMeter()
    token = _current.set(meter)
    try:
        yield meter
    finally:
        _current.reset(token)
