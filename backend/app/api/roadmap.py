"""
Roadmap Generation API Route
=============================
Endpoint:
    POST /generate-roadmap

Generates a structured startup roadmap with milestones, sprints, MVP phases,
and a calendar-style execution timeline. Persists to Supabase when an
authenticated user is present.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user_id
from app.models.roadmap import GenerateRoadmapRequest, GenerateRoadmapResponse
from app.services.openai_service import (
    OpenAIInvalidResponseError,
    OpenAINotConfiguredError,
    OpenAIServiceError,
)
from app.services.roadmap_service import RoadmapService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Roadmap"])


def get_roadmap_service() -> RoadmapService:
    """Factory for the roadmap orchestration service (overridable in tests)."""
    return RoadmapService()


@router.post(
    "/generate-roadmap",
    response_model=GenerateRoadmapResponse,
    summary="Generate and persist a structured startup roadmap",
    description=(
        "Generates a comprehensive startup roadmap including milestones, sprint-by-sprint "
        "plan, MVP phases, and a full execution timeline. Output is a strictly validated "
        "JSON structure. When an authenticated user is present, the roadmap is auto-saved "
        "to Supabase and linked to a project (created on the fly if needed)."
    ),
    responses={
        200: {"description": "Roadmap generated successfully"},
        422: {"description": "Request validation failed"},
        502: {"description": "Upstream OpenAI error or invalid JSON from model"},
        503: {"description": "OpenAI is not configured on the server"},
        500: {"description": "Unexpected server error"},
    },
)
async def generate_roadmap(
    request: GenerateRoadmapRequest,
    service: RoadmapService = Depends(get_roadmap_service),
    user_id: Optional[str] = Depends(get_current_user_id),
) -> GenerateRoadmapResponse:
    logger.info(
        f"POST /generate-roadmap — industry={request.industry!r}, "
        f"timeline={request.timeline_weeks}w, team={request.team_size}, "
        f"user_id={user_id or 'anonymous'}"
    )

    try:
        result = await service.generate_and_persist(
            startup_idea=request.startup_idea,
            target_audience=request.target_audience,
            industry=request.industry,
            timeline_weeks=request.timeline_weeks,
            team_size=request.team_size,
            sprint_length_weeks=request.sprint_length_weeks,
            user_id=user_id,
            project_id=request.project_id,
            project_name=request.project_name,
        )

    except OpenAINotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "openai_not_configured", "message": str(exc)},
        )
    except OpenAIInvalidResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "invalid_model_response",
                "message": "The AI model returned an invalid roadmap response.",
                "details": str(exc),
            },
        )
    except OpenAIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "openai_service_error", "message": str(exc)},
        )
    except Exception:
        logger.exception("Unexpected error generating roadmap")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while generating the roadmap.",
            },
        )

    return GenerateRoadmapResponse(
        roadmap=result.roadmap,
        model=result.model,
        startup_idea=request.startup_idea,
        target_audience=request.target_audience,
        industry=request.industry,
        timeline_weeks=request.timeline_weeks,
        team_size=request.team_size,
        persisted=result.persisted,
        user_id=result.user_id,
        project_id=result.project_id,
        generation_id=result.generation_id,
        warnings=result.warnings,
        persistence_error=result.persistence_error,
    )
