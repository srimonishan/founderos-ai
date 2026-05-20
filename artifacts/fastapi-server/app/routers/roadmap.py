from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.dependencies import get_openai_client, get_supabase_client
from app.schemas.roadmap import RoadmapRequest, RoadmapResponse
from app.services.openai_service import OpenAIService
from app.services.supabase_service import SupabaseService


router = APIRouter(tags=["Generations"])


@router.post(
    "/generate-roadmap",
    response_model=RoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a Product Roadmap",
    description="Generates a phased product roadmap with milestones and resource estimates.",
)
async def generate_roadmap(request: RoadmapRequest) -> RoadmapResponse:
    openai_client = get_openai_client()
    supabase_client = get_supabase_client()

    openai_service = OpenAIService(openai_client)
    supabase_service = SupabaseService(supabase_client)

    try:
        roadmap_content = await openai_service.generate_roadmap(
            idea_title=request.idea_title,
            description=request.description,
            timeline_months=request.timeline_months,
            team_size=request.team_size,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate roadmap: {str(e)}",
        )

    generation_id = None
    if request.user_id and settings.is_supabase_configured:
        try:
            saved = await supabase_service.save_generation(
                generation_type="roadmap",
                input_data=request.model_dump(exclude={"user_id"}),
                output_content=roadmap_content,
                user_id=request.user_id,
            )
            generation_id = saved.get("id")
        except Exception:
            pass

    return RoadmapResponse(
        success=True,
        idea_title=request.idea_title,
        roadmap_content=roadmap_content,
        timeline_months=request.timeline_months,
        team_size=request.team_size,
        model=settings.OPENAI_MODEL,
        generation_id=generation_id,
    )
