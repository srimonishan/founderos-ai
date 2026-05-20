from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GenerationType(str, Enum):
    PRD = "prd"
    ROADMAP = "roadmap"
    ARCHITECTURE = "architecture"
    PITCH_DECK = "pitch_deck"
    MARKET_ANALYSIS = "market_analysis"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── PRD ───────────────────────────────────────────────────────────────────────

class PRDRequest(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    target_market: str = Field(..., min_length=5, max_length=500)
    problem_statement: str = Field(..., min_length=20, max_length=1000)
    user_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "idea_title": "FounderOS AI",
                "description": "AI-powered platform that helps founders validate ideas and execute faster.",
                "target_market": "Early-stage founders, 1-10 person teams",
                "problem_statement": "Founders spend weeks on documentation instead of shipping.",
            }
        }
    }


class PRDResponse(BaseModel):
    success: bool = True
    idea_title: str
    prd_content: str
    model: str
    generation_id: Optional[str] = None


# ── Roadmap ───────────────────────────────────────────────────────────────────

class RoadmapRequest(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    timeline_months: int = Field(default=12, ge=1, le=60)
    team_size: int = Field(default=3, ge=1, le=100)
    user_id: Optional[str] = None


class RoadmapResponse(BaseModel):
    success: bool = True
    idea_title: str
    roadmap_content: str
    timeline_months: int
    team_size: int
    model: str
    generation_id: Optional[str] = None


# ── Architecture ──────────────────────────────────────────────────────────────

class ArchitectureRequest(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    tech_preferences: str = Field(default="Modern cloud-native stack", max_length=500)
    scale_requirements: str = Field(default="Start small, scale to 100k users", max_length=500)
    user_id: Optional[str] = None


class ArchitectureResponse(BaseModel):
    success: bool = True
    idea_title: str
    architecture_content: str
    model: str
    generation_id: Optional[str] = None


# ── Stored Generation Record ──────────────────────────────────────────────────

class GenerationRecord(BaseModel):
    id: str
    type: GenerationType
    status: GenerationStatus
    input_data: Dict[str, Any]
    output_content: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
