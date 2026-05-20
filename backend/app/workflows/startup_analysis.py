import asyncio
import logging
from typing import Any, Dict

from app.models.workflow import FullStartupAnalysisRequest, FullStartupAnalysisResponse
from app.services.openai_service import OpenAIService
from app.services.supabase_service import SupabaseService
from app.core.config import settings
from app.workflows.base import BaseWorkflow

logger = logging.getLogger(__name__)


class StartupAnalysisWorkflow(BaseWorkflow):
    """
    Full startup analysis workflow.

    Steps:
      1. Generate PRD
      2. Generate Roadmap  (parallel with step 3)
      3. Generate Architecture  (parallel with step 2)
      4. Persist all results to Supabase
    """

    name = "startup_analysis"

    def __init__(self):
        super().__init__()
        self.openai = OpenAIService()
        self.supabase = SupabaseService()

    async def run_steps(self, input_data: Dict[str, Any]) -> None:
        request = FullStartupAnalysisRequest(**input_data)

        # Step 1 — PRD (must come first; roadmap and architecture can reference it)
        prd = await self.run_step(
            "prd", "Generate Product Requirements Document",
            self.openai.generate_prd(
                idea_title=request.idea_title,
                description=request.description,
                target_market=request.target_market,
                problem_statement=request.problem_statement,
            ),
        )

        # Steps 2 & 3 — Roadmap + Architecture in parallel
        roadmap, architecture = await asyncio.gather(
            self.run_step(
                "roadmap", "Generate Product Roadmap",
                self.openai.generate_roadmap(
                    idea_title=request.idea_title,
                    description=request.description,
                    timeline_months=request.timeline_months,
                    team_size=request.team_size,
                ),
            ),
            self.run_step(
                "architecture", "Generate System Architecture",
                self.openai.generate_architecture(
                    idea_title=request.idea_title,
                    description=request.description,
                    tech_preferences=request.tech_preferences,
                    scale_requirements="Start small, scale to 100k users",
                ),
            ),
        )

        # Step 4 — Persist (fire-and-forget, non-blocking)
        await self.run_step(
            "persist", "Save results to database",
            self._persist_all(request, prd, roadmap, architecture),
        )

        self.run.output_data = {
            "prd": prd,
            "roadmap": roadmap,
            "architecture": architecture,
        }

    async def _persist_all(
        self,
        request: FullStartupAnalysisRequest,
        prd: str,
        roadmap: str,
        architecture: str,
    ) -> None:
        if not settings.is_supabase_configured:
            return

        base_input = {
            "idea_title": request.idea_title,
            "description": request.description,
        }

        await asyncio.gather(
            self.supabase.save_generation("prd", base_input, prd, request.user_id, self.run_id),
            self.supabase.save_generation("roadmap", base_input, roadmap, request.user_id, self.run_id),
            self.supabase.save_generation("architecture", base_input, architecture, request.user_id, self.run_id),
        )
