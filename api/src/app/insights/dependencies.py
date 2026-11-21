"""FastAPI dependencies for the insights module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.insights.repository import SqlInsightsRepository
from app.insights.service import InsightsService
from app.llm.factory import get_llm_client
from app.llm.port import LLMClient


def get_insights_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> InsightsService:
    """Construct an InsightsService backed by PostgreSQL and the chosen LLM."""
    return InsightsService(repo=SqlInsightsRepository(db), llm=llm)
