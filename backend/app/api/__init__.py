"""
API Router Registry
====================
Single source of truth for mounting all API routers onto the FastAPI app.

Adding a new route module is a one-line change:
  1. Create your router in `app/api/<feature>.py` (or `app/api/v1/endpoints/<feature>.py`).
  2. Add an entry to `ROUTERS` below.

The application factory in `app.main` calls `register_routers(app)` — it never
needs to know about individual modules. This keeps `main.py` stable and
encourages a flat, scalable feature-folder layout.
"""

from dataclasses import dataclass
from typing import List, Optional

from fastapi import APIRouter, FastAPI

# ── Import all feature routers here ──────────────────────────────────────────
from app.api.prd import router as prd_router
from app.api.v1.router import api_router as v1_router


@dataclass(frozen=True)
class RouterMount:
    """Declarative description of how a router should be mounted."""
    router: APIRouter
    prefix: str = ""
    tags: Optional[List[str]] = None
    description: str = ""


# ── Mount table ──────────────────────────────────────────────────────────────
# Order is preserved in the registration log. Most-specific prefixes first.
ROUTERS: List[RouterMount] = [
    RouterMount(
        router=v1_router,
        prefix="/api/v1",
        description="Versioned API (generations, workflows, health)",
    ),
    RouterMount(
        router=prd_router,
        prefix="",
        description="Standalone PRD endpoint at /generate-prd",
    ),
]


def register_routers(app: FastAPI) -> None:
    """Mount every router in ROUTERS onto the given FastAPI app."""
    import logging
    logger = logging.getLogger(__name__)

    for mount in ROUTERS:
        app.include_router(mount.router, prefix=mount.prefix, tags=mount.tags or [])
        logger.info(
            f"  ↳ mounted {mount.prefix or '/'} — {mount.description}"
        )


__all__ = ["register_routers", "ROUTERS", "RouterMount"]
