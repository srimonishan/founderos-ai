from typing import Optional
from pydantic import BaseModel, Field


class RoadmapRequest(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=200, description="Title of the product")
    description: str = Field(..., min_length=20, max_length=2000, description="Product description")
    timeline_months: int = Field(default=12, ge=1, le=60, description="Target timeline in months")
    team_size: int = Field(default=3, ge=1, le=100, description="Number of people on the team")
    user_id: Optional[str] = Field(None, description="Optional user ID to save the result")

    model_config = {
        "json_schema_extra": {
            "example": {
                "idea_title": "FounderOS AI",
                "description": "AI-powered startup execution platform",
                "timeline_months": 12,
                "team_size": 4,
                "user_id": None,
            }
        }
    }


class RoadmapResponse(BaseModel):
    success: bool
    idea_title: str
    roadmap_content: str
    timeline_months: int
    team_size: int
    model: str
    generation_id: Optional[str] = None
