from typing import Optional
from pydantic import BaseModel, Field


class ArchitectureRequest(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=200, description="Title of the product")
    description: str = Field(..., min_length=20, max_length=2000, description="Product description")
    tech_preferences: str = Field(
        default="Modern cloud-native stack",
        max_length=500,
        description="Preferred technologies or constraints",
    )
    scale_requirements: str = Field(
        default="Start small, scale to 100k users",
        max_length=500,
        description="Expected scale and performance requirements",
    )
    user_id: Optional[str] = Field(None, description="Optional user ID to save the result")

    model_config = {
        "json_schema_extra": {
            "example": {
                "idea_title": "FounderOS AI",
                "description": "AI-powered startup execution platform",
                "tech_preferences": "Python FastAPI backend, React frontend, PostgreSQL, Redis",
                "scale_requirements": "MVP for 1k users, scalable to 500k users",
                "user_id": None,
            }
        }
    }


class ArchitectureResponse(BaseModel):
    success: bool
    idea_title: str
    architecture_content: str
    model: str
    generation_id: Optional[str] = None
