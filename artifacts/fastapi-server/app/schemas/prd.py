from typing import Optional
from pydantic import BaseModel, Field


class PRDRequest(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=200, description="Title of the startup idea")
    description: str = Field(..., min_length=20, max_length=2000, description="Detailed description of the product")
    target_market: str = Field(..., min_length=5, max_length=500, description="Target market and customer segment")
    problem_statement: str = Field(..., min_length=20, max_length=1000, description="Core problem being solved")
    user_id: Optional[str] = Field(None, description="Optional user ID to save the result")

    model_config = {
        "json_schema_extra": {
            "example": {
                "idea_title": "FounderOS AI",
                "description": "An AI-powered platform that helps founders validate ideas, generate PRDs, and execute on their startup vision.",
                "target_market": "Early-stage founders and startup teams of 1-10 people",
                "problem_statement": "Founders waste weeks on documentation and planning instead of building and shipping.",
                "user_id": None,
            }
        }
    }


class PRDResponse(BaseModel):
    success: bool
    idea_title: str
    prd_content: str
    model: str
    generation_id: Optional[str] = None
    tokens_used: Optional[int] = None
