from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class WorkflowStep(BaseModel):
    step_id: str
    name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class WorkflowRun(BaseModel):
    run_id: str
    workflow_name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = []
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    user_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class FullStartupAnalysisRequest(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    target_market: str = Field(..., min_length=5, max_length=500)
    problem_statement: str = Field(..., min_length=20, max_length=1000)
    timeline_months: int = Field(default=12, ge=1, le=60)
    team_size: int = Field(default=3, ge=1, le=100)
    tech_preferences: str = Field(default="Modern cloud-native stack", max_length=500)
    user_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "idea_title": "FounderOS AI",
                "description": "AI-powered startup execution platform for ambitious founders.",
                "target_market": "Early-stage founders and startup teams",
                "problem_statement": "Founders waste weeks on planning instead of building.",
                "timeline_months": 12,
                "team_size": 4,
                "tech_preferences": "Python FastAPI, React, PostgreSQL, Redis",
            }
        }
    }


class FullStartupAnalysisResponse(BaseModel):
    success: bool = True
    run_id: str
    idea_title: str
    prd: str
    roadmap: str
    architecture: str
    workflow_run: WorkflowRun
