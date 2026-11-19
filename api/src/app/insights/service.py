"""Business logic service for on-demand query insights (US-12)."""

import uuid

from app.core.errors import NotFound
from app.insights.repository import InsightsRepository
from app.insights.schemas import InsightsPayload
from app.llm.port import LLMClient
from app.prompts.loader import load_prompt
from app.sessions.schemas import SessionRecord


class InsightsService:
    """Generates and caches grounded insights for an owned query run."""

    def __init__(self, repo: InsightsRepository, llm: LLMClient) -> None:
        self._repo = repo
        self._llm = llm

    async def generate(self, session: SessionRecord, query_run_id: uuid.UUID) -> InsightsPayload:
        """Return cached insights or generate new ones via the LLMClient port."""
        run = await self._repo.get_query_run(session.id, query_run_id)
        if run is None:
            raise NotFound("Query run not found.")

        cached = await self._repo.get_cached_insights(query_run_id)
        if cached is not None:
            return cached

        system_prompt = load_prompt("insights", version="v1")
        user_prompt = (
            f"Question: {run.question}\n"
            f"SQL: {run.generated_sql or 'N/A'}\n"
            f"Rows returned: {run.row_count}"
        )
        payload = await self._llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=InsightsPayload,
        )
        await self._repo.save_insights(query_run_id, payload)
        return payload
