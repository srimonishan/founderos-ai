from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.dependencies import get_openai_client, get_supabase_client
from app.schemas.architecture import ArchitectureRequest, ArchitectureResponse
from app.services.openai_service import OpenAIService
from app.services.supabase_service import SupabaseService


router = APIRouter(tags=["Generations"])


@router.post(
    "/generate-architecture",
    response_model=ArchitectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a System Architecture",
    description="Generates a production-ready system architecture document for a startup.",
)
async def generate_architecture(request: ArchitectureRequest) -> ArchitectureResponse:
    openai_client = get_openai_client()
    supabase_client = get_supabase_client()

    openai_service = OpenAIService(openai_client)
    supabase_service = SupabaseService(supabase_client)

    try:
        architecture_content = await openai_service.generate_architecture(
            idea_title=request.idea_title,
            description=request.description,
            tech_preferences=request.tech_preferences,
            scale_requirements=request.scale_requirements,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate architecture: {str(e)}",
        )

    generation_id = None
    if request.user_id and settings.is_supabase_configured:
        try:
            saved = await supabase_service.save_generation(
                generation_type="architecture",
                input_data=request.model_dump(exclude={"user_id"}),
                output_content=architecture_content,
                user_id=request.user_id,
            )
            generation_id = saved.get("id")
        except Exception:
            pass

    return ArchitectureResponse(
        success=True,
        idea_title=request.idea_title,
        architecture_content=architecture_content,
        model=settings.OPENAI_MODEL,
        generation_id=generation_id,
    )
