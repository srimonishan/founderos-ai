import json
import logging
from typing import Optional

from app.models.generation import (
    PRDRequest, PRDResponse,
    RoadmapRequest, RoadmapResponse,
    ArchitectureRequest, ArchitectureResponse,
)
from app.services.openai_service import OpenAIService
from app.services.supabase_service import SupabaseService
from app.core.config import settings

logger = logging.getLogger(__name__)


class GenerationService:
    """Orchestrates AI generation requests end-to-end (call OpenAI + persist to DB)."""

    def __init__(self):
        self.openai = OpenAIService()
        self.supabase = SupabaseService()

    async def generate_prd(self, request: PRDRequest) -> PRDResponse:
        logger.info(f"Generating PRD for industry='{request.industry}'")

        prd = await self.openai.generate_prd(
            startup_idea=request.startup_idea,
            target_audience=request.target_audience,
            industry=request.industry,
        )

        # Persist as JSON so we can re-render the structured output later
        generation_id = await self._persist(
            "prd",
            request.model_dump(exclude={"user_id"}),
            json.dumps(prd.model_dump(), indent=2),
            request.user_id,
        )

        return PRDResponse(
            startup_idea=request.startup_idea,
            target_audience=request.target_audience,
            industry=request.industry,
            prd=prd,
            model=settings.OPENAI_MODEL,
            generation_id=generation_id,
        )

    async def generate_roadmap(self, request: RoadmapRequest) -> RoadmapResponse:
        logger.info(f"Generating roadmap for: {request.idea_title}")

        content = await self.openai.generate_roadmap(
            idea_title=request.idea_title,
            description=request.description,
            timeline_months=request.timeline_months,
            team_size=request.team_size,
        )

        generation_id = await self._persist(
            "roadmap", request.model_dump(exclude={"user_id"}), content, request.user_id
        )

        return RoadmapResponse(
            idea_title=request.idea_title,
            roadmap_content=content,
            timeline_months=request.timeline_months,
            team_size=request.team_size,
            model=settings.OPENAI_MODEL,
            generation_id=generation_id,
        )

    async def generate_architecture(self, request: ArchitectureRequest) -> ArchitectureResponse:
        logger.info(f"Generating architecture for: {request.idea_title}")

        content = await self.openai.generate_architecture(
            idea_title=request.idea_title,
            description=request.description,
            tech_preferences=request.tech_preferences,
            scale_requirements=request.scale_requirements,
        )

        generation_id = await self._persist(
            "architecture", request.model_dump(exclude={"user_id"}), content, request.user_id
        )

        return ArchitectureResponse(
            idea_title=request.idea_title,
            architecture_content=content,
            model=settings.OPENAI_MODEL,
            generation_id=generation_id,
        )

    async def _persist(
        self,
        gen_type: str,
        input_data: dict,
        content: str,
        user_id: Optional[str],
        workflow_run_id: Optional[str] = None,
    ) -> Optional[str]:
        if not settings.is_supabase_configured:
            return None
        try:
            saved = await self.supabase.save_generation(
                generation_type=gen_type,
                input_data=input_data,
                output_content=content,
                user_id=user_id,
                workflow_run_id=workflow_run_id,
            )
            return saved.get("id")
        except Exception as exc:
            logger.warning(f"Failed to persist generation ({gen_type}): {exc}")
            return None
