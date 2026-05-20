"""
Architecture Generation — Pydantic Models
==========================================
Structured JSON schema for AI-generated software architecture plans.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class ComponentPriority(str, Enum):
    CORE = "core"
    IMPORTANT = "important"
    OPTIONAL = "optional"


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


# ── Frontend ─────────────────────────────────────────────────────────────────

class FrontendComponent(BaseModel):
    name: str
    purpose: str
    type: str = Field(..., description="e.g. 'page', 'feature', 'shared-ui', 'layout'")


class FrontendArchitecture(BaseModel):
    framework: str = Field(..., description="Recommended framework (e.g. 'React + Vite', 'Next.js')")
    language: str = Field(default="TypeScript")
    styling: str = Field(..., description="e.g. 'Tailwind CSS', 'CSS Modules'")
    state_management: str = Field(..., description="e.g. 'TanStack Query + Zustand'")
    routing: str = Field(..., description="e.g. 'React Router', 'Next.js App Router'")
    key_libraries: List[str] = Field(..., min_length=1)
    folder_structure: List[str] = Field(..., min_length=1, description="Top-level folders/conventions")
    key_components: List[FrontendComponent] = Field(..., min_length=2)
    rationale: str = Field(..., description="Why this stack fits the project")


# ── Backend ──────────────────────────────────────────────────────────────────

class BackendService(BaseModel):
    name: str
    responsibility: str
    type: str = Field(..., description="e.g. 'http-api', 'worker', 'scheduler', 'webhook-handler'")


class BackendArchitecture(BaseModel):
    framework: str = Field(..., description="e.g. 'FastAPI', 'Express', 'NestJS'")
    language: str = Field(..., description="e.g. 'Python 3.12', 'Node.js 24'")
    runtime: str = Field(..., description="e.g. 'Uvicorn ASGI', 'Node.js'")
    pattern: str = Field(..., description="e.g. 'modular monolith', 'service-oriented'")
    key_libraries: List[str] = Field(..., min_length=1)
    services: List[BackendService] = Field(..., min_length=1)
    background_jobs: List[str] = Field(default_factory=list, description="Async/queued workloads")
    auth_strategy: str = Field(..., description="e.g. 'Supabase JWT', 'OAuth2 + JWT'")
    rationale: str


# ── Database ─────────────────────────────────────────────────────────────────

class DatabaseColumn(BaseModel):
    name: str
    type: str = Field(..., description="SQL type (e.g. 'uuid', 'text', 'timestamptz', 'jsonb')")
    nullable: bool = Field(default=False)
    description: Optional[str] = None


class DatabaseTable(BaseModel):
    name: str
    purpose: str
    columns: List[DatabaseColumn] = Field(..., min_length=2)
    indexes: List[str] = Field(default_factory=list, description="Recommended indexes (column names or expressions)")
    relationships: List[str] = Field(default_factory=list, description="FK relationships in plain English")


class DatabaseArchitecture(BaseModel):
    engine: str = Field(..., description="e.g. 'PostgreSQL 16 (Supabase)'")
    orm: Optional[str] = Field(None, description="e.g. 'SQLAlchemy', 'Drizzle', 'Prisma'")
    tables: List[DatabaseTable] = Field(..., min_length=2)
    migration_strategy: str = Field(..., description="How schema changes are applied")
    backup_strategy: Optional[str] = None
    rationale: str


# ── API endpoints ────────────────────────────────────────────────────────────

class APIEndpoint(BaseModel):
    method: HTTPMethod
    path: str = Field(..., description="e.g. '/api/v1/projects/{id}'")
    summary: str = Field(..., description="What this endpoint does")
    auth_required: bool = Field(default=True)
    request_shape: Optional[str] = Field(None, description="High-level body schema sketch")
    response_shape: Optional[str] = Field(None, description="High-level response schema sketch")


class APIPlan(BaseModel):
    style: str = Field(..., description="e.g. 'REST', 'tRPC', 'GraphQL'")
    base_url: str = Field(default="/api/v1")
    endpoints: List[APIEndpoint] = Field(..., min_length=3)
    versioning_strategy: str = Field(..., description="How API versions are managed")
    error_format: str = Field(..., description="Error response convention")


# ── Engineering recommendations ──────────────────────────────────────────────

class EngineeringRecommendation(BaseModel):
    area: str = Field(..., description="e.g. 'observability', 'testing', 'deployment', 'security'")
    recommendation: str
    priority: ComponentPriority


class InfrastructurePlan(BaseModel):
    hosting: str = Field(..., description="e.g. 'Replit Deployments', 'Vercel + Fly.io'")
    cdn: Optional[str] = None
    caching_strategy: str = Field(..., description="e.g. 'TanStack Query client-side; Redis later for hot reads'")
    observability: str = Field(..., description="Logging/metrics/tracing approach")
    ci_cd: str = Field(..., description="Build & deploy pipeline approach")


# ── Top-level output ─────────────────────────────────────────────────────────

class ArchitectureOutput(BaseModel):
    executive_summary: str = Field(..., description="2-3 sentence overview of the proposed architecture")
    frontend: FrontendArchitecture
    backend: BackendArchitecture
    database: DatabaseArchitecture
    api_plan: APIPlan
    infrastructure: InfrastructurePlan
    engineering_recommendations: List[EngineeringRecommendation] = Field(..., min_length=3)
    scalability_notes: str = Field(..., description="How the architecture scales from MVP to growth")
    security_notes: str = Field(..., description="Key security considerations")


# ── Request / Response wrappers ──────────────────────────────────────────────

class GenerateArchitectureRequest(BaseModel):
    startup_idea: str = Field(..., min_length=10, max_length=2000)
    target_audience: str = Field(..., min_length=3, max_length=500)
    industry: str = Field(..., min_length=2, max_length=100)

    expected_scale: str = Field(
        default="mvp",
        description="e.g. 'mvp', 'early-growth', 'scale' — guides infra recommendations",
    )
    preferred_stack: Optional[str] = Field(
        None, max_length=200,
        description="Optional stack preference hint (e.g. 'Python + React')",
    )

    # Persistence hints
    project_id: Optional[str] = None
    project_name: Optional[str] = Field(None, max_length=120)

    model_config = {
        "json_schema_extra": {
            "example": {
                "startup_idea": "AI-powered platform that generates PRDs, roadmaps, and "
                                "architecture plans for early-stage founders.",
                "target_audience": "Solo founders and small startup teams",
                "industry": "SaaS / Developer Tools",
                "expected_scale": "mvp",
                "preferred_stack": "Python + React",
            }
        }
    }


class GenerateArchitectureResponse(BaseModel):
    success: bool = True
    architecture: ArchitectureOutput
    model: str

    startup_idea: str
    target_audience: str
    industry: str
    expected_scale: str

    persisted: bool = False
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    generation_id: Optional[str] = None
    warnings: List[str] = []
    persistence_error: Optional[str] = None
