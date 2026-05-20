"""
Roadmap Generation — Pydantic Models
=====================================
Structured JSON schema for AI-generated startup roadmaps.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class MilestonePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MVPPhaseStatus(str, Enum):
    DISCOVERY = "discovery"
    DESIGN = "design"
    BUILD = "build"
    BETA = "beta"
    LAUNCH = "launch"
    SCALE = "scale"


# ── Nested structures ────────────────────────────────────────────────────────

class Milestone(BaseModel):
    """A single startup milestone."""
    name: str = Field(..., description="Concise milestone name")
    description: str = Field(..., description="1-2 sentence explanation of the milestone")
    target_date: str = Field(..., description="Target date or relative timing (e.g. 'Week 6', 'Month 3', 'Q2 2026')")
    priority: MilestonePriority
    owner: Optional[str] = Field(None, description="Suggested role responsible (e.g. 'CTO', 'Founder')")
    success_metric: str = Field(..., description="How success is measured")


class Sprint(BaseModel):
    """A 1-2 week sprint within the roadmap."""
    sprint_number: int = Field(..., ge=1, description="Sprint number (1-indexed)")
    name: str = Field(..., description="Sprint theme or focus")
    duration_weeks: int = Field(default=2, ge=1, le=4)
    goals: List[str] = Field(..., min_length=1, description="2-5 concrete goals for this sprint")
    deliverables: List[str] = Field(..., min_length=1, description="Tangible outputs from this sprint")
    risks: List[str] = Field(default_factory=list, description="Known risks or blockers")


class MVPPhase(BaseModel):
    """A high-level phase of the MVP build."""
    phase: MVPPhaseStatus
    name: str = Field(..., description="Human-readable phase name")
    timeline: str = Field(..., description="e.g. 'Weeks 1-3', 'Month 2'")
    objectives: List[str] = Field(..., min_length=1, description="What this phase achieves")
    key_features: List[str] = Field(default_factory=list, description="Features built in this phase")
    exit_criteria: str = Field(..., description="What signals readiness to move to the next phase")


class TimelineEntry(BaseModel):
    """A single dated point on the execution timeline."""
    timeframe: str = Field(..., description="e.g. 'Week 1-2', 'Month 1', 'Q1 2026'")
    focus: str = Field(..., description="Headline activity for this period")
    key_outcomes: List[str] = Field(..., min_length=1, description="Outcomes delivered by end of timeframe")


# ── Top-level output ─────────────────────────────────────────────────────────

class RoadmapOutput(BaseModel):
    """Structured roadmap returned by OpenAIService.generate_structured_roadmap()."""
    executive_summary: str = Field(..., description="2-3 sentence summary of the roadmap")
    milestones: List[Milestone] = Field(..., min_length=3, description="Key startup milestones")
    sprint_roadmap: List[Sprint] = Field(..., min_length=2, description="Sprint-by-sprint breakdown")
    mvp_phases: List[MVPPhase] = Field(..., min_length=2, description="MVP build phases")
    execution_timeline: List[TimelineEntry] = Field(..., min_length=3, description="Calendar-style execution timeline")
    total_duration_weeks: int = Field(..., ge=1, le=104, description="Total roadmap length in weeks")
    risk_summary: Optional[str] = Field(None, description="Cross-cutting risks and mitigation notes")


# ── Request / Response wrappers ──────────────────────────────────────────────

class GenerateRoadmapRequest(BaseModel):
    """Body schema for POST /generate-roadmap."""
    startup_idea: str = Field(..., min_length=10, max_length=2000)
    target_audience: str = Field(..., min_length=3, max_length=500)
    industry: str = Field(..., min_length=2, max_length=100)

    timeline_weeks: int = Field(default=24, ge=4, le=104,
                                description="Total roadmap length in weeks (default: 24)")
    team_size: int = Field(default=3, ge=1, le=100)
    sprint_length_weeks: int = Field(default=2, ge=1, le=4)

    # Persistence hints
    project_id: Optional[str] = None
    project_name: Optional[str] = Field(None, max_length=120)

    model_config = {
        "json_schema_extra": {
            "example": {
                "startup_idea": "AI-powered platform that helps founders generate PRDs, "
                                "roadmaps, and architecture plans in minutes.",
                "target_audience": "Solo founders and small startup teams",
                "industry": "SaaS / Developer Tools",
                "timeline_weeks": 24,
                "team_size": 3,
                "sprint_length_weeks": 2,
            }
        }
    }


class GenerateRoadmapResponse(BaseModel):
    """Envelope returned by POST /generate-roadmap."""
    success: bool = True
    roadmap: RoadmapOutput
    model: str

    startup_idea: str
    target_audience: str
    industry: str
    timeline_weeks: int
    team_size: int

    persisted: bool = False
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    generation_id: Optional[str] = None
    warnings: List[str] = []
    persistence_error: Optional[str] = None
