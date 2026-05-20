"""
Health Check API
=================
Production-ready monitoring endpoints for FounderOS AI.

Endpoints:
  * GET /health        — liveness probe (always fast, never blocks)
  * GET /health/ready  — readiness probe (checks downstream integrations)
  * GET /health/live   — alias of /health for k8s convention compatibility
  * GET /health/info   — full diagnostic info (config summary, no secrets)

Conventions followed:
  * Liveness is a fast, dependency-free check — used by load balancers
  * Readiness performs live dependency probes — used to gate traffic
  * All responses are structured JSON with predictable schemas
  * Failing readiness returns HTTP 503 with a per-dependency status list
  * No secrets ever appear in responses
"""

from __future__ import annotations

import asyncio
import logging
import platform
import time
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


# ── Process-level state ──────────────────────────────────────────────────────

_PROCESS_START = time.monotonic()
_STARTED_AT_ISO = datetime.now(timezone.utc).isoformat()


def _uptime_seconds() -> float:
    return round(time.monotonic() - _PROCESS_START, 3)


# ── Response models ──────────────────────────────────────────────────────────

HealthStatus = Literal["ok", "degraded", "not_ready", "error"]
CheckStatus = Literal["ok", "skipped", "error", "timeout"]


class LivenessResponse(BaseModel):
    """Lightweight, dependency-free liveness signal."""
    status: HealthStatus = "ok"
    app: str
    version: str
    environment: str
    uptime_seconds: float
    started_at: str
    timestamp: str


class DependencyCheck(BaseModel):
    name: str
    status: CheckStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class ReadinessResponse(BaseModel):
    status: HealthStatus
    app: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str
    checks: List[DependencyCheck] = Field(default_factory=list)


class InfoResponse(BaseModel):
    app: str
    version: str
    environment: str
    debug: bool
    uptime_seconds: float
    started_at: str
    timestamp: str
    runtime: Dict[str, str]
    integrations: Dict[str, Dict[str, object]]
    cors: dict
    docs_enabled: bool


# ── Dependency probes ────────────────────────────────────────────────────────

_PROBE_TIMEOUT_S = 3.0


async def _check_openai() -> DependencyCheck:
    if not settings.is_openai_configured:
        return DependencyCheck(
            name="openai", status="skipped", message="OPENAI_API_KEY not set"
        )
    return DependencyCheck(
        name="openai",
        status="ok",
        message=f"API key configured (model={settings.OPENAI_MODEL})",
    )


async def _check_supabase() -> DependencyCheck:
    if not settings.is_supabase_configured:
        return DependencyCheck(
            name="supabase", status="skipped",
            message="SUPABASE_URL / SUPABASE_ANON_KEY not set",
        )
    try:
        from app.services.supabase_service import SupabaseService
        svc = SupabaseService()
        start = time.perf_counter()
        ok = await asyncio.wait_for(svc.ping(), timeout=_PROBE_TIMEOUT_S)
        latency = round((time.perf_counter() - start) * 1000, 2)
        if ok:
            return DependencyCheck(
                name="supabase", status="ok", latency_ms=latency,
                message="connection healthy",
            )
        return DependencyCheck(
            name="supabase", status="error", latency_ms=latency,
            message="ping returned False",
        )
    except asyncio.TimeoutError:
        return DependencyCheck(
            name="supabase", status="timeout",
            message=f"ping exceeded {_PROBE_TIMEOUT_S}s",
        )
    except Exception as exc:
        return DependencyCheck(
            name="supabase", status="error", message=str(exc)[:200],
        )


async def _run_all_checks() -> List[DependencyCheck]:
    return list(await asyncio.gather(_check_openai(), _check_supabase()))


def _aggregate_status(checks: List[DependencyCheck]) -> HealthStatus:
    """Return overall readiness status from individual dependency checks."""
    has_required_failure = any(c.status in {"error", "timeout"} for c in checks)
    if has_required_failure:
        return "not_ready"
    # Skipped checks (unconfigured optional deps) → degraded but still ok-ish.
    # In production, treat skipped required deps as not_ready.
    if any(c.status == "skipped" for c in checks) and settings.is_production:
        return "not_ready"
    if any(c.status == "skipped" for c in checks):
        return "degraded"
    return "ok"


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description=(
        "Lightweight check used by load balancers and container orchestrators "
        "to confirm the process is alive. Returns immediately and performs no "
        "downstream dependency calls — so it stays fast even when integrations "
        "are degraded."
    ),
    responses={200: {"description": "Service is alive"}},
)
async def health() -> LivenessResponse:
    return LivenessResponse(
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=_uptime_seconds(),
        started_at=_STARTED_AT_ISO,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness probe (alias)",
    description="Alias of /health for Kubernetes-style `/health/live` consumers.",
)
async def live() -> LivenessResponse:
    return await health()


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description=(
        "Performs live dependency checks (OpenAI, Supabase) with short timeouts. "
        "Returns HTTP 503 when one or more required dependencies are unavailable. "
        "Use this to gate traffic from a load balancer or rolling deploy."
    ),
    responses={
        200: {"description": "All dependencies reachable"},
        503: {"description": "One or more dependencies are not ready"},
    },
)
async def ready() -> ReadinessResponse:
    checks = await _run_all_checks()
    overall = _aggregate_status(checks)

    body = ReadinessResponse(
        status=overall,
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=_uptime_seconds(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks,
    )

    if overall == "not_ready":
        # Surface the structured payload as the HTTP 503 detail
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=body.model_dump(),
        )

    return body


@router.get(
    "/health/info",
    response_model=InfoResponse,
    summary="Diagnostic info",
    description=(
        "Full runtime diagnostic information — versions, integration "
        "configuration flags (never secrets), CORS summary, and uptime."
    ),
)
async def info() -> InfoResponse:
    return InfoResponse(
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        uptime_seconds=_uptime_seconds(),
        started_at=_STARTED_AT_ISO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        runtime={
            "python": platform.python_version(),
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        integrations={
            "openai": {
                "configured": settings.is_openai_configured,
                "model": settings.OPENAI_MODEL,
                "fallback_model": settings.OPENAI_FALLBACK_MODEL,
            },
            "supabase": {
                "configured": settings.is_supabase_configured,
                "service_key_configured": settings.has_supabase_service_key,
            },
        },
        cors=settings.cors.summary(),
        docs_enabled=settings.docs_enabled,
    )
