"""
Architecture Generation API Route
==================================
Endpoint:
    POST /generate-architecture

Generates a structured software architecture plan including frontend, backend,
database schema, API plan, infrastructure, and engineering recommendations.
Persists to Supabase when an authenticated user is present.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user_id
from app.models.architecture import (
    GenerateArchitectureRequest,
    GenerateArchitectureResponse,
)
from app.services.architecture_service import ArchitectureService
from app.services.openai_service import (
    OpenAIInvalidResponseError,
    OpenAINotConfiguredError,
    OpenAIServiceError,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Architecture"])


def get_architecture_service() -> ArchitectureService:
    """Factory for the architecture orchestration service (overridable in tests)."""
    return ArchitectureService()


@router.post(
    "/generate-architecture",
    response_model=GenerateArchitectureResponse,
    summary="Generate and persist a structured software architecture plan",
    description=(
        "Generates a comprehensive software architecture plan including frontend stack, "
        "backend services, database schema, REST API endpoint plan, infrastructure, "
        "scalability, and security recommendations. Output is strictly validated JSON. "
        "Auto-saved to Supabase and linked to a project when authenticated."
    ),
    responses={
        200: {"description": "Architecture generated successfully"},
        422: {"description": "Request validation failed"},
        502: {"description": "Upstream OpenAI error or invalid JSON from model"},
        503: {"description": "OpenAI is not configured on the server"},
        500: {"description": "Unexpected server error"},
    },
)
async def generate_architecture(
    request: GenerateArchitectureRequest,
    service: ArchitectureService = Depends(get_architecture_service),
    user_id: Optional[str] = Depends(get_current_user_id),
) -> GenerateArchitectureResponse:
    logger.info(
        f"POST /generate-architecture — industry={request.industry!r}, "
        f"scale={request.expected_scale!r}, user_id={user_id or 'anonymous'}"
    )

    try:
        result = await service.generate_and_persist(
            startup_idea=request.startup_idea,
            target_audience=request.target_audience,
            industry=request.industry,
            expected_scale=request.expected_scale,
            preferred_stack=request.preferred_stack,
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
                "message": "The AI model returned an invalid architecture response.",
                "details": str(exc),
            },
        )
    except OpenAIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "openai_service_error", "message": str(exc)},
        )
    except Exception:
        logger.exception("Unexpected error generating architecture")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while generating the architecture.",
            },
        )

    return GenerateArchitectureResponse(
        architecture=result.architecture,
        model=result.model,
        startup_idea=request.startup_idea,
        target_audience=request.target_audience,
        industry=request.industry,
        expected_scale=request.expected_scale,
        persisted=result.persisted,
        user_id=result.user_id,
        project_id=result.project_id,
        generation_id=result.generation_id,
        warnings=result.warnings,
        persistence_error=result.persistence_error,
    )
