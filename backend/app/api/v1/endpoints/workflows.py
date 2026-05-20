from fastapi import APIRouter, HTTPException, status

from app.models.workflow import FullStartupAnalysisRequest, FullStartupAnalysisResponse
from app.workflows.startup_analysis import StartupAnalysisWorkflow

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post(
    "/analyze",
    response_model=FullStartupAnalysisResponse,
    summary="Full Startup Analysis",
    description=(
        "Runs the complete startup analysis workflow: PRD first, then Roadmap and Architecture "
        "in parallel. Returns all three documents plus a full workflow execution trace."
    ),
)
async def run_startup_analysis(request: FullStartupAnalysisRequest) -> FullStartupAnalysisResponse:
    workflow = StartupAnalysisWorkflow()

    try:
        run = await workflow.execute(request.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    output = run.output_data

    return FullStartupAnalysisResponse(
        run_id=run.run_id,
        idea_title=request.idea_title,
        prd=output["prd"],
        roadmap=output["roadmap"],
        architecture=output["architecture"],
        workflow_run=run,
    )
