"""
Architecture Orchestration Service
===================================
Composes OpenAI structured-architecture generation with Supabase persistence.
Mirrors PRDService and RoadmapService for consistency.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.core.config import settings
from app.models.architecture import ArchitectureOutput
from app.services.openai_service import OpenAIService
from app.services.supabase_service import SupabaseNotConfiguredError, SupabaseService

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureGenerationResult:
    architecture: ArchitectureOutput
    model: str
    persisted: bool = False
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    generation_id: Optional[str] = None
    created_at: Optional[datetime] = None
    persistence_error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class ArchitectureService:
    """Orchestrates architecture generation across OpenAI + Supabase."""

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
        expected_scale: str = "mvp",
        preferred_stack: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> ArchitectureGenerationResult:
        architecture = await self.openai.generate_structured_architecture(
            startup_idea=startup_idea,
            target_audience=target_audience,
            industry=industry,
            expected_scale=expected_scale,
            preferred_stack=preferred_stack,
        )

        logger.info(
            f"Architecture generated — fe={architecture.frontend.framework}, "
            f"be={architecture.backend.framework}, "
            f"tables={len(architecture.database.tables)}, "
            f"endpoints={len(architecture.api_plan.endpoints)}"
        )

        result = ArchitectureGenerationResult(
            architecture=architecture,
            model=settings.OPENAI_MODEL,
            user_id=user_id,
            project_id=project_id,
            created_at=datetime.now(timezone.utc),
        )

        if not user_id:
            result.warnings.append("No user_id provided — architecture not persisted.")
            return result

        if not settings.is_supabase_configured:
            result.warnings.append("Supabase not configured — architecture not persisted.")
            return result

        try:
            await self._persist(
                result=result,
                startup_idea=startup_idea,
                target_audience=target_audience,
                industry=industry,
                expected_scale=expected_scale,
                preferred_stack=preferred_stack,
                project_name=project_name,
            )
        except SupabaseNotConfiguredError as exc:
            result.persistence_error = str(exc)
        except Exception as exc:
            result.persistence_error = str(exc)
            logger.warning(f"Architecture persistence failed (non-fatal): {exc}")

        return result

    async def _persist(
        self,
        *,
        result: ArchitectureGenerationResult,
        startup_idea: str,
        target_audience: str,
        industry: str,
        expected_scale: str,
        preferred_stack: Optional[str],
        project_name: Optional[str],
    ) -> None:
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

        arch = result.architecture
        arch_dict = arch.model_dump()
        metadata = {
            "frontend_framework": arch.frontend.framework,
            "backend_framework": arch.backend.framework,
            "database_engine": arch.database.engine,
            "table_count": len(arch.database.tables),
            "endpoint_count": len(arch.api_plan.endpoints),
            "service_count": len(arch.backend.services),
            "recommendation_count": len(arch.engineering_recommendations),
            "expected_scale": expected_scale,
        }

        saved = await self.supabase.save_generation(
            generation_type="architecture",
            input_data={
                "startup_idea": startup_idea,
                "target_audience": target_audience,
                "industry": industry,
                "expected_scale": expected_scale,
                "preferred_stack": preferred_stack,
            },
            output_content=json.dumps(arch_dict, indent=2),
            user_id=result.user_id,
            project_id=result.project_id,
            metadata=metadata,
        )

        result.generation_id = saved.get("id")
        result.persisted = True
        logger.info(
            f"Persisted architecture — generation_id={result.generation_id}, "
            f"project_id={result.project_id}"
        )


def _derive_project_name(startup_idea: str, max_len: int = 60) -> str:
    first_sentence = startup_idea.split(".")[0].strip()
    if len(first_sentence) <= max_len:
        return first_sentence or "Untitled Project"
    return first_sentence[: max_len - 1].rstrip() + "…"
