from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings


router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    openai_configured: bool
    supabase_configured: bool


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        openai_configured=settings.is_openai_configured,
        supabase_configured=settings.is_supabase_configured,
    )
