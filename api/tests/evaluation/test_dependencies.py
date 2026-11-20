"""Unit tests for evaluation dependency wiring (US-14)."""

from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.evaluation.dependencies import get_eval_service
from app.evaluation.golden_sets import GOLDEN_SETS
from app.evaluation.repository import SqlEvalRepository
from app.evaluation.runner import LlmEvalRunner
from app.llm.factory import describe_llm


class NullLLM:
    async def generate_structured(self, **_: Any) -> Any:
        raise AssertionError("not called during wiring")


def test_eval_service_uses_database_repository_and_llm_runner() -> None:
    settings = Settings(llm_provider="gemini", gemini_model="gemini-2.5-flash")
    service = get_eval_service(
        db=cast(AsyncSession, object()), settings=settings, llm=NullLLM()
    )

    assert isinstance(service.repository, SqlEvalRepository)
    assert isinstance(service.build_runner(GOLDEN_SETS["retail_sales"]), LlmEvalRunner)
    assert service.model_name == "gemini:gemini-2.5-flash"


def test_describe_llm_reports_provider_and_model() -> None:
    settings = Settings()

    assert describe_llm(settings) == f"ollama:{settings.ollama_model}"
    assert describe_llm(settings, provider="claude", model="m") == "claude:m"
