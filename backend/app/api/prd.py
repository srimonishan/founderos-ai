"""
PRD Generation API Route
=========================
Standalone PRD endpoint mounted at the app root.

Endpoint:
    POST /generate-prd

Request body (JSON):
    {
        "startup_idea":    "...",     # required, 10-2000 chars
        "target_audience": "...",     # required, 3-500 chars
        "industry":        "..."      # required, 2-100 chars
    }

Returns a fully structured PRD (see PRDOutput schema).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.models.generation import PRDOutput
from app.services.openai_service import (
    OpenAIService,
    OpenAINotConfiguredError,
    OpenAIInvalidResponseError,
    OpenAIServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["PRD"])


# ── Request / Response models (route-local) ───────────────────────────────────

class GeneratePRDRequest(BaseModel):
    """Body schema for POST /generate-prd."""

    startup_idea: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="One-paragraph description of the startup idea",
    )
    target_audience: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Who the product is for (e.g. 'Solo founders in B2B SaaS')",
    )
    industry: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Industry or vertical (e.g. 'FinTech', 'Developer Tools')",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "startup_idea": (
                    "AI-powered platform that helps early-stage founders generate PRDs, "
                    "roadmaps, and architecture plans in minutes instead of weeks."
                ),
                "target_audience": "Solo founders and 1-10 person startup teams",
                "industry": "SaaS / Developer Tools",
            }
        }
    }


class GeneratePRDResponse(BaseModel):
    """Envelope returned by POST /generate-prd."""

    success: bool = True
    startup_idea: str
    target_audience: str
    industry: str
    prd: PRDOutput
    model: str
    generation_id: Optional[str] = None


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post(
    "/generate-prd",
    response_model=GeneratePRDResponse,
    summary="Generate a structured Product Requirements Document",
    description=(
        "Uses GPT-4o (with gpt-4o-mini fallback) to produce a fully structured PRD "
        "including startup summary, core features, monetization strategy, and roadmap. "
        "Output is validated against a strict Pydantic schema."
    ),
    responses={
        200: {"description": "PRD generated successfully"},
        422: {"description": "Request validation failed"},
        502: {"description": "Upstream OpenAI error or invalid JSON from model"},
        503: {"description": "OpenAI is not configured on the server"},
        500: {"description": "Unexpected server error"},
    },
)
async def generate_prd(request: GeneratePRDRequest) -> GeneratePRDResponse:
    """Generate a structured PRD from a startup idea, target audience, and industry."""
    logger.info(
        f"POST /generate-prd — industry={request.industry!r}, "
        f"audience={request.target_audience[:60]!r}"
    )

    service = OpenAIService()

    try:
        prd = await service.generate_prd(
            startup_idea=request.startup_idea,
            target_audience=request.target_audience,
            industry=request.industry,
        )

    except OpenAINotConfiguredError as exc:
        logger.error(f"OpenAI not configured: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "openai_not_configured",
                "message": str(exc),
            },
        )

    except OpenAIInvalidResponseError as exc:
        logger.error(f"Invalid PRD response from model: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "invalid_model_response",
                "message": "The AI model returned an invalid or malformed response.",
                "details": str(exc),
            },
        )

    except OpenAIServiceError as exc:
        logger.error(f"OpenAI service error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "openai_service_error",
                "message": str(exc),
            },
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

    logger.info(
        f"PRD generated — features={len(prd.core_features)}, "
        f"tiers={len(prd.monetization_strategy.pricing_tiers)}, "
        f"phases={len(prd.roadmap_overview)}"
    )

    return GeneratePRDResponse(
        startup_idea=request.startup_idea,
        target_audience=request.target_audience,
        industry=request.industry,
        prd=prd,
        model=settings.OPENAI_MODEL,
    )
