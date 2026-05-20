"""
Roadmap Orchestration Service
==============================
Composes OpenAI structured-roadmap generation with Supabase persistence.

Mirrors the PRDService architecture for consistency.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.core.config import settings
from app.models.roadmap import RoadmapOutput
from app.services.openai_service import OpenAIService
from app.services.supabase_service import SupabaseNotConfiguredError, SupabaseService

logger = logging.getLogger(__name__)


@dataclass
class RoadmapGenerationResult:
    roadmap: RoadmapOutput
    model: str
    persisted: bool = False
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    generation_id: Optional[str] = None
    created_at: Optional[datetime] = None
    persistence_error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class RoadmapService:
    """Orchestrates roadmap generation across OpenAI + Supabase."""

    def __init__(
        self,
        openai: Optional[OpenAIService] = None,
        supabase: Optional[SupabaseService] = None,
    ):
        self.openai = openai or OpenAIService()
        self.supabase = supabase or SupabaseService()

    async def generate_and_persist(
        self,
        *,
        startup_idea: str,
        target_audience: str,
        industry: str,
        timeline_weeks: int = 24,
        team_size: int = 3,
        sprint_length_weeks: int = 2,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> RoadmapGenerationResult:
        roadmap = await self.openai.generate_structured_roadmap(
            startup_idea=startup_idea,
            target_audience=target_audience,
            industry=industry,
            timeline_weeks=timeline_weeks,
            team_size=team_size,
            sprint_length_weeks=sprint_length_weeks,
        )

        logger.info(
            f"Roadmap generated — milestones={len(roadmap.milestones)}, "
            f"sprints={len(roadmap.sprint_roadmap)}, "
            f"mvp_phases={len(roadmap.mvp_phases)}, "
            f"timeline_entries={len(roadmap.execution_timeline)}"
        )

        result = RoadmapGenerationResult(
            roadmap=roadmap,
            model=settings.OPENAI_MODEL,
            user_id=user_id,
            project_id=project_id,
            created_at=datetime.now(timezone.utc),
        )

        if not user_id:
            result.warnings.append("No user_id provided — roadmap not persisted.")
            return result

        if not settings.is_supabase_configured:
            result.warnings.append("Supabase not configured — roadmap not persisted.")
            return result

        try:
            await self._persist(
                result=result,
                startup_idea=startup_idea,
                target_audience=target_audience,
                industry=industry,
                timeline_weeks=timeline_weeks,
                team_size=team_size,
                project_name=project_name,
            )
        except SupabaseNotConfiguredError as exc:
            result.persistence_error = str(exc)
        except Exception as exc:
            result.persistence_error = str(exc)
            logger.warning(f"Roadmap persistence failed (non-fatal): {exc}")

        return result

    async def _persist(
        self,
        *,
        result: RoadmapGenerationResult,
        startup_idea: str,
        target_audience: str,
        industry: str,
        timeline_weeks: int,
        team_size: int,
        project_name: Optional[str],
    ) -> None:
        # Resolve project (reuse if provided, otherwise create one)
        if not result.project_id:
            project = await self.supabase.create_project(
                user_id=result.user_id,
                name=project_name or _derive_project_name(startup_idea),
                description=startup_idea,
                industry=industry,
                target_audience=target_audience,
            )
            result.project_id = project.get("id")
            logger.info(f"Created project {result.project_id} for user {result.user_id}")

        roadmap_dict = result.roadmap.model_dump()
        metadata = {
            "milestone_count": len(roadmap_dict.get("milestones", [])),
            "sprint_count": len(roadmap_dict.get("sprint_roadmap", [])),
            "mvp_phase_count": len(roadmap_dict.get("mvp_phases", [])),
            "total_duration_weeks": roadmap_dict.get("total_duration_weeks"),
            "timeline_weeks_requested": timeline_weeks,
            "team_size": team_size,
        }

        saved = await self.supabase.save_generation(
            generation_type="roadmap",
            input_data={
                "startup_idea": startup_idea,
                "target_audience": target_audience,
                "industry": industry,
                "timeline_weeks": timeline_weeks,
                "team_size": team_size,
            },
            output_content=json.dumps(roadmap_dict, indent=2),
            user_id=result.user_id,
            project_id=result.project_id,
            metadata=metadata,
        )

        result.generation_id = saved.get("id")
        result.persisted = True
        logger.info(
            f"Persisted roadmap — generation_id={result.generation_id}, "
            f"project_id={result.project_id}"
        )


def _derive_project_name(startup_idea: str, max_len: int = 60) -> str:
    first_sentence = startup_idea.split(".")[0].strip()
    if len(first_sentence) <= max_len:
        return first_sentence or "Untitled Project"
    return first_sentence[: max_len - 1].rstrip() + "…"
