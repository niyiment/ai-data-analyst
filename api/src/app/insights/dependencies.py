"""FastAPI dependencies for the insights module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.insights.repository import SqlInsightsRepository
from app.insights.service import InsightsService
from app.llm.gemini import GeminiLLMClient


def get_insights_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InsightsService:
    """Construct an InsightsService backed by PostgreSQL and Gemini."""
    return InsightsService(
        repo=SqlInsightsRepository(db),
        llm=GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model),
    )
