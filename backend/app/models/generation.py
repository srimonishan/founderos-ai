from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

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


class FeaturePriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


# ─────────────────────────────────────────────────────────────────────────────
# PRD — structured JSON output
# ─────────────────────────────────────────────────────────────────────────────

class PRDFeature(BaseModel):
    name: str = Field(..., description="Short feature name")
    description: str = Field(..., description="1-2 sentence description of what the feature does")
    priority: FeaturePriority = Field(..., description="P0 = must-have, P1 = important, P2 = nice-to-have")


class PricingTier(BaseModel):
    name: str = Field(..., description="Tier name (e.g. 'Starter', 'Pro', 'Enterprise')")
    price_usd_per_month: float = Field(..., ge=0, description="Monthly price in USD, 0 for free tier")
    target_segment: str = Field(..., description="Which customer segment this tier targets")
    key_features: List[str] = Field(default_factory=list, description="Features included in this tier")


class MonetizationStrategy(BaseModel):
    revenue_model: str = Field(..., description="e.g. 'B2B SaaS subscription', 'Usage-based', 'Marketplace fees'")
    pricing_tiers: List[PricingTier] = Field(..., min_length=1)
    notes: Optional[str] = Field(None, description="Additional monetization notes or considerations")


class RoadmapPhase(BaseModel):
    phase: str = Field(..., description="Phase name (e.g. 'MVP', 'Beta', 'Public Launch', 'Scale')")
    timeline: str = Field(..., description="Human-readable timeline (e.g. 'Months 1-3', 'Q2 2026')")
    milestones: List[str] = Field(..., min_length=1, description="Key milestones for this phase")


class PRDOutput(BaseModel):
    """Structured PRD response returned by OpenAIService.generate_prd()."""
    startup_summary: str = Field(..., description="2-3 sentence executive summary of the startup")
    core_features: List[PRDFeature] = Field(..., min_length=1, description="The product's core features")
    monetization_strategy: MonetizationStrategy
    roadmap_overview: List[RoadmapPhase] = Field(..., min_length=1, description="High-level roadmap phases")


# ── PRD — request/response wrappers ───────────────────────────────────────────

class PRDRequest(BaseModel):
    startup_idea: str = Field(..., min_length=10, max_length=2000, description="The startup idea description")
    target_audience: str = Field(..., min_length=3, max_length=500, description="Who the product is for")
    industry: str = Field(..., min_length=2, max_length=100, description="Industry / vertical")
    user_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "startup_idea": "AI-powered platform that helps early-stage founders generate PRDs, roadmaps, and architecture plans in minutes instead of weeks.",
                "target_audience": "Solo founders and 1-10 person startup teams",
                "industry": "SaaS / Developer Tools",
            }
        }
    }


class PRDResponse(BaseModel):
    success: bool = True
    startup_idea: str
    target_audience: str
    industry: str
    prd: PRDOutput
    model: str
    generation_id: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Roadmap (markdown output, used by full-analysis workflow)
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Architecture (markdown output, used by full-analysis workflow)
# ─────────────────────────────────────────────────────────────────────────────

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
