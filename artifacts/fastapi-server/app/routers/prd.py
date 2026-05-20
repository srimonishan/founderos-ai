from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.dependencies import get_openai_client, get_supabase_client
from app.schemas.prd import PRDRequest, PRDResponse
from app.services.openai_service import OpenAIService
from app.services.supabase_service import SupabaseService


router = APIRouter(tags=["Generations"])


@router.post(
    "/generate-prd",
    response_model=PRDResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a Product Requirements Document",
    description="Takes a startup idea and generates a comprehensive PRD using AI.",
)
async def generate_prd(request: PRDRequest) -> PRDResponse:
    openai_client = get_openai_client()
    supabase_client = get_supabase_client()

    openai_service = OpenAIService(openai_client)
    supabase_service = SupabaseService(supabase_client)

    try:
        prd_content = await openai_service.generate_prd(
            idea_title=request.idea_title,
            description=request.description,
            target_market=request.target_market,
            problem_statement=request.problem_statement,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PRD: {str(e)}",
        )

    generation_id = None
    if request.user_id and settings.is_supabase_configured:
        try:
            saved = await supabase_service.save_generation(
                generation_type="prd",
                input_data=request.model_dump(exclude={"user_id"}),
                output_content=prd_content,
                user_id=request.user_id,
            )
            generation_id = saved.get("id")
        except Exception:
            pass

    return PRDResponse(
        success=True,
        idea_title=request.idea_title,
        prd_content=prd_content,
        model=settings.OPENAI_MODEL,
        generation_id=generation_id,
    )
