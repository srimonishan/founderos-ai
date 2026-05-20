"""
FounderOS AI — FastAPI Application Entry Point
===============================================
Initializes the app, registers all middleware, mounts versioned API routers,
and exposes health check endpoints.
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import register_routers
from app.core.config import settings
from app.core.errors import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    setup_logging()

    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"  environment : {settings.ENVIRONMENT}")
    logger.info(f"  port        : {settings.PORT}")
    logger.info(f"  debug       : {settings.DEBUG}")
    logger.info(f"  openai      : {'✓' if settings.is_openai_configured else '✗ (not configured)'}")
    logger.info(f"  supabase    : {'✓' if settings.is_supabase_configured else '✗ (not configured)'}")
    logger.info(f"  docs        : {'enabled' if settings.docs_enabled else 'disabled (production)'}")
    logger.info("=" * 60)

    yield

    logger.info(f"[{settings.APP_NAME}] Shutting down gracefully")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    Kept as a factory function so tests can create isolated instances.
    """
    _app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered startup execution platform. "
            "Generate PRDs, roadmaps, architecture plans, "
            "and run multi-step parallel AI workflows."
        ),
        version=settings.APP_VERSION,
        # Disable interactive docs in production
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    _register_middleware(_app)
    _register_exception_handlers(_app)
    _register_routers(_app)

    return _app


# ── Middleware ────────────────────────────────────────────────────────────────

def _register_middleware(app: FastAPI) -> None:
    # 1. Gzip compression for large AI-generated responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 2. CORS — production-ready: explicit origins + tightly-scoped regex
    #    (Replit prod/dev, Vercel previews, optional FRONTEND_URL, EXTRA_CORS_ORIGINS).
    cors = settings.cors
    logger.info(
        f"CORS: {len(cors.allow_origins)} origin(s), "
        f"regex={'on' if cors.allow_origin_regex else 'off'}, "
        f"credentials={cors.allow_credentials}"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors.allow_origins,
        allow_origin_regex=cors.allow_origin_regex,
        allow_credentials=cors.allow_credentials,
        allow_methods=cors.allow_methods,
        allow_headers=cors.allow_headers,
        expose_headers=cors.expose_headers,
        max_age=cors.max_age,
    )

    # 3. Trusted hosts (permissive for Replit's proxied environment)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )

    # 4. Request timing + request-id injection
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", "")

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        if request_id:
            response.headers["X-Request-ID"] = request_id

        logger.debug(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
        )
        return response


# ── Exception handlers ────────────────────────────────────────────────────────

def _register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


# ── Routers ───────────────────────────────────────────────────────────────────

def _register_routers(app: FastAPI) -> None:
    """Delegate router registration to the central API registry."""
    logger.info("Registering API routers:")
    register_routers(app)


# ── Health endpoints ──────────────────────────────────────────────────────────

def _register_health(app: FastAPI) -> None:
    """Registered separately so health routes are never blocked by auth middleware."""
    pass


# Instantiate the app
app = create_app()


@app.get("/health", tags=["Health"], summary="Liveness check")
async def health() -> dict:
    """
    Lightweight liveness probe — returns immediately.
    Use this for load-balancer and container health checks.
    """
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health/ready", tags=["Health"], summary="Readiness check")
async def ready() -> dict:
    """
    Readiness probe — confirms all downstream integrations are configured.
    Returns HTTP 503 if a required service is unavailable.
    """
    issues = []
    if not settings.is_openai_configured:
        issues.append("OPENAI_API_KEY not set")
    if not settings.is_supabase_configured:
        issues.append("SUPABASE_URL / SUPABASE_ANON_KEY not set")

    if issues:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "issues": issues},
        )

    return {
        "status": "ready",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "integrations": {
            "openai": {"configured": True, "model": settings.OPENAI_MODEL},
            "supabase": {"configured": True, "url": settings.SUPABASE_URL},
        },
    }


@app.get("/health/info", tags=["Health"], summary="Full diagnostic info")
async def info() -> dict:
    """Detailed runtime information — disable in production if sensitive."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "openai": {
            "configured": settings.is_openai_configured,
            "model": settings.OPENAI_MODEL,
            "fallback_model": settings.OPENAI_FALLBACK_MODEL,
        },
        "supabase": {
            "configured": settings.is_supabase_configured,
        },
        "cors": settings.cors.summary(),
        "docs_enabled": settings.docs_enabled,
    }


# ── Dev entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=not settings.is_production,
        proxy_headers=True,          # respect X-Forwarded-* from Replit's proxy
        forwarded_allow_ips="*",
    )
