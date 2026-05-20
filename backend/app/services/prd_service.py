"""
PRD Orchestration Service
==========================
Thin composition layer that ties OpenAI generation to Supabase persistence.

Responsibilities:
  * Generate the structured PRD via OpenAIService
  * Resolve / create the project that owns it
  * Persist the PRD generation record linked to user + project
  * Return a single dataclass result the API layer can serialize

Persistence is best-effort: if Supabase is unconfigured or a write fails,
the PRD is still returned to the caller. This keeps the AI generation flow
robust to database outages.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.models.generation import PRDOutput
from app.services.openai_service import OpenAIService
from app.services.supabase_service import (
    SupabaseNotConfiguredError,
    SupabaseService,
)

logger = logging.getLogger(__name__)


# ── Result type ──────────────────────────────────────────────────────────────

@dataclass
class PRDGenerationResult:
    """Result of an end-to-end PRD generation + persistence operation."""
    prd: PRDOutput
    model: str
    persisted: bool = False
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    generation_id: Optional[str] = None
    created_at: Optional[datetime] = None
    persistence_error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


# ── Service ──────────────────────────────────────────────────────────────────

class PRDService:
    """Orchestrates PRD generation across OpenAI + Supabase."""

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
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> PRDGenerationResult:
        """
        Generate a structured PRD and (best-effort) persist it.

        Persistence flow when `user_id` is provided:
          1. If `project_id` is supplied → use it as-is
          2. Else create a new project owned by the user
          3. Save the PRD via `supabase.save_prd()` linked to user + project
        """
        # ── 1. Generate via OpenAI (hard requirement) ────────────────────────
        prd = await self.openai.generate_prd(
            startup_idea=startup_idea,
            target_audience=target_audience,
            industry=industry,
        )

        logger.info(
            f"PRD generated — features={len(prd.core_features)}, "
            f"tiers={len(prd.monetization_strategy.pricing_tiers)}, "
            f"phases={len(prd.roadmap_overview)}"
        )

        result = PRDGenerationResult(
            prd=prd,
            model=settings.OPENAI_MODEL,
            user_id=user_id,
            project_id=project_id,
            created_at=datetime.now(timezone.utc),
        )

        # ── 2. Persist (best-effort) ─────────────────────────────────────────
        if not user_id:
            result.warnings.append("No user_id provided — PRD not persisted.")
            return result

        if not settings.is_supabase_configured:
            result.warnings.append("Supabase not configured — PRD not persisted.")
            return result

        try:
            await self._persist(
                result=result,
                startup_idea=startup_idea,
                target_audience=target_audience,
                industry=industry,
                project_name=project_name,
            )
        except SupabaseNotConfiguredError as exc:
            result.persistence_error = str(exc)
            logger.warning(f"Supabase unavailable, skipping persistence: {exc}")
        except Exception as exc:
            result.persistence_error = str(exc)
            logger.warning(f"PRD persistence failed (non-fatal): {exc}")

        return result

    # ── Internal ─────────────────────────────────────────────────────────────

    async def _persist(
        self,
        *,
        result: PRDGenerationResult,
        startup_idea: str,
        target_audience: str,
        industry: str,
        project_name: Optional[str],
    ) -> None:
        """Resolve project, then save the PRD generation row."""
        # Resolve project: use provided id, else create one
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

        # Save the PRD generation
        saved = await self.supabase.save_prd(
            prd=result.prd,
            user_id=result.user_id,
            project_id=result.project_id,
            input_data={
                "startup_idea": startup_idea,
                "target_audience": target_audience,
                "industry": industry,
            },
        )
        result.generation_id = saved.get("id")
        result.persisted = True

        if saved.get("created_at"):
            try:
                result.created_at = datetime.fromisoformat(
                    saved["created_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        logger.info(
            f"Persisted PRD — generation_id={result.generation_id}, "
            f"project_id={result.project_id}, user_id={result.user_id}"
        )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _derive_project_name(startup_idea: str, max_len: int = 60) -> str:
    """Take the first sentence (or `max_len` chars) as the project name."""
    first_sentence = startup_idea.split(".")[0].strip()
    if len(first_sentence) <= max_len:
        return first_sentence or "Untitled Project"
    return first_sentence[: max_len - 1].rstrip() + "…"
