"""
PRD Generation API Route
=========================
Standalone PRD endpoint mounted at the app root.

Endpoint:
    POST /generate-prd

Request body (JSON):
    {
        "startup_idea":    "...",    # required, 10-2000 chars
        "target_audience": "...",    # required, 3-500 chars
        "industry":        "...",    # required, 2-100 chars
        "project_id":      "...",    # optional — link the PRD to an existing project
        "project_name":    "..."     # optional — name to use when auto-creating the project
    }

Authentication (optional but recommended for persistence):
    Authorization: Bearer <supabase-jwt>
    OR
    X-User-Id: <uuid>

Returns the structured PRD plus persistence metadata
(generation_id, project_id, persisted flag).
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user_id
from app.models.generation import PRDOutput
from app.services.openai_service import (
    OpenAIInvalidResponseError,
    OpenAINotConfiguredError,
    OpenAIServiceError,
)
from app.services.prd_service import PRDService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["PRD"])


# ── Request / Response models ────────────────────────────────────────────────

class GeneratePRDRequest(BaseModel):
    """Body schema for POST /generate-prd."""

    startup_idea: str = Field(..., min_length=10, max_length=2000,
                              description="One-paragraph description of the startup idea")
    target_audience: str = Field(..., min_length=3, max_length=500,
                                 description="Who the product is for")
    industry: str = Field(..., min_length=2, max_length=100,
                          description="Industry or vertical")

    # Optional persistence hints
    project_id: Optional[str] = Field(
        None, description="Existing project ID to attach this PRD to. "
                          "If omitted, a new project is created automatically."
    )
    project_name: Optional[str] = Field(
        None, max_length=120,
        description="Name for the auto-created project (ignored if project_id is set)."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "startup_idea": (
                    "AI-powered platform that helps early-stage founders generate "
                    "PRDs, roadmaps, and architecture plans in minutes instead of weeks."
                ),
                "target_audience": "Solo founders and 1-10 person startup teams",
                "industry": "SaaS / Developer Tools",
                "project_name": "FounderOS AI",
            }
        }
    }


class GeneratePRDResponse(BaseModel):
    """Envelope returned by POST /generate-prd."""

    success: bool = True
    prd: PRDOutput
    model: str

    # Echo of the inputs for client convenience
    startup_idea: str
    target_audience: str
    industry: str

    # Persistence metadata
    persisted: bool = False
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    generation_id: Optional[str] = None
    created_at: Optional[datetime] = None
    warnings: list[str] = []
    persistence_error: Optional[str] = None


# ── Dependency injection ─────────────────────────────────────────────────────

def get_prd_service() -> PRDService:
    """Factory for the PRD orchestration service. Easy to override in tests."""
    return PRDService()


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post(
    "/generate-prd",
    response_model=GeneratePRDResponse,
    summary="Generate and persist a structured Product Requirements Document",
    description=(
        "Generates a PRD via OpenAI and, when an authenticated user is present, "
        "auto-creates a startup project and persists the PRD to Supabase. "
        "Persistence is best-effort — the PRD is always returned even if the "
        "database write fails."
    ),
    responses={
        200: {"description": "PRD generated successfully"},
        422: {"description": "Request validation failed"},
        502: {"description": "Upstream OpenAI error or invalid JSON from model"},
        503: {"description": "OpenAI is not configured on the server"},
        500: {"description": "Unexpected server error"},
    },
)
async def generate_prd(
    request: GeneratePRDRequest,
    service: PRDService = Depends(get_prd_service),
    user_id: Optional[str] = Depends(get_current_user_id),
) -> GeneratePRDResponse:
    """Generate a structured PRD and (best-effort) persist it for the user."""
    logger.info(
        f"POST /generate-prd — industry={request.industry!r}, "
        f"user_id={user_id or 'anonymous'}, project_id={request.project_id or 'auto'}"
    )

    try:
        result = await service.generate_and_persist(
            startup_idea=request.startup_idea,
            target_audience=request.target_audience,
            industry=request.industry,
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
                "message": "The AI model returned an invalid response.",
                "details": str(exc),
            },
        )
    except OpenAIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "openai_service_error", "message": str(exc)},
        )
    except Exception as exc:
        logger.exception("Unexpected error generating PRD")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while generating the PRD.",
            },
        )

    return GeneratePRDResponse(
        prd=result.prd,
        model=result.model,
        startup_idea=request.startup_idea,
        target_audience=request.target_audience,
        industry=request.industry,
        persisted=result.persisted,
        user_id=result.user_id,
        project_id=result.project_id,
        generation_id=result.generation_id,
        created_at=result.created_at,
        warnings=result.warnings,
        persistence_error=result.persistence_error,
    )
