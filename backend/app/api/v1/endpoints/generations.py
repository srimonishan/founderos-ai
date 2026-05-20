from fastapi import APIRouter, HTTPException, status

from app.models.generation import (
    PRDRequest, PRDResponse,
    RoadmapRequest, RoadmapResponse,
    ArchitectureRequest, ArchitectureResponse,
)
from app.services.generation_service import GenerationService

router = APIRouter(prefix="/generate", tags=["Generations"])


def _svc() -> GenerationService:
    return GenerationService()


@router.post("/prd", response_model=PRDResponse, summary="Generate Product Requirements Document")
async def generate_prd(request: PRDRequest) -> PRDResponse:
    try:
        return await _svc().generate_prd(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/roadmap", response_model=RoadmapResponse, summary="Generate Product Roadmap")
async def generate_roadmap(request: RoadmapRequest) -> RoadmapResponse:
    try:
        return await _svc().generate_roadmap(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/architecture", response_model=ArchitectureResponse, summary="Generate System Architecture")
async def generate_architecture(request: ArchitectureRequest) -> ArchitectureResponse:
    try:
        return await _svc().generate_architecture(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
