"""
Supabase Database Service
=========================
Reusable async-friendly wrapper around the Supabase Python client.

Tables managed:
  * users          — user profile data (linked to auth.users)
  * projects       — startup projects owned by a user
  * generations    — AI-generated artefacts (PRDs, roadmaps, architectures, etc.)
  * workflow_runs  — multi-step AI workflow execution records

Conventions:
  * All methods are `async def` and use `asyncio.to_thread()` to keep the
    synchronous supabase-py client off the event loop.
  * Methods never raise on missing config — they raise `SupabaseNotConfiguredError`,
    which the caller can catch to make persistence optional.
  * All write methods return the inserted/updated row as a dict.

Environment variables (loaded via `app.core.config.settings`):
  * SUPABASE_URL
  * SUPABASE_ANON_KEY
  * SUPABASE_SERVICE_KEY  (preferred for server-side writes; required for RLS bypass)
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from supabase import Client

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Exceptions ────────────────────────────────────────────────────────────────

class SupabaseServiceError(Exception):
    """Base error for Supabase service operations."""


class SupabaseNotConfiguredError(SupabaseServiceError):
    """Raised when SUPABASE_URL or SUPABASE_ANON_KEY is missing."""


class SupabaseRecordNotFoundError(SupabaseServiceError):
    """Raised when a `_one` lookup finds no matching row."""


# ── Table names (single source of truth) ──────────────────────────────────────

class Tables:
    USERS = "users"
    PROJECTS = "projects"
    GENERATIONS = "generations"
    WORKFLOW_RUNS = "workflow_runs"


# ── Service ───────────────────────────────────────────────────────────────────

class SupabaseService:
    """
    Reusable database service. Inject into routes/workflows like:

        svc = SupabaseService()
        project = await svc.create_project(name="My SaaS", user_id=user.id)
        await svc.save_prd(project_id=project["id"], prd=prd_output, user_id=user.id)
    """

    def __init__(self, client: Optional[Client] = None):
        from app.core.dependencies import get_supabase_client
        self.client = client or get_supabase_client()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _require_client(self) -> Client:
        if not self.client:
            raise SupabaseNotConfiguredError(
                "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY "
                "(and SUPABASE_SERVICE_KEY for server-side writes that bypass RLS)."
            )
        return self.client

    async def _exec(self, builder) -> Any:
        """Run a sync supabase query builder in a worker thread."""
        return await asyncio.to_thread(builder.execute)

    @staticmethod
    def _first(response) -> Optional[Dict[str, Any]]:
        data = getattr(response, "data", None) or []
        return data[0] if data else None

    @staticmethod
    def _all(response) -> List[Dict[str, Any]]:
        return getattr(response, "data", None) or []

    # ─────────────────────────────────────────────────────────────────────────
    # Users
    # ─────────────────────────────────────────────────────────────────────────

    async def upsert_user(
        self,
        user_id: str,
        email: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create or update a user profile (idempotent on user_id)."""
        client = self._require_client()
        record = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "avatar_url": avatar_url,
            "metadata": metadata or {},
            "updated_at": _now_iso(),
        }
        record = _strip_none(record)
        response = await self._exec(
            client.table(Tables.USERS).upsert(record, on_conflict="id")
        )
        return self._first(response) or {}

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.USERS).select("*").eq("id", user_id).limit(1)
        )
        return self._first(response)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.USERS).select("*").eq("email", email).limit(1)
        )
        return self._first(response)

    # ─────────────────────────────────────────────────────────────────────────
    # Projects
    # ─────────────────────────────────────────────────────────────────────────

    async def create_project(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        target_audience: Optional[str] = None,
        status: str = "active",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        client = self._require_client()
        record = _strip_none({
            "user_id": user_id,
            "name": name,
            "description": description,
            "industry": industry,
            "target_audience": target_audience,
            "status": status,
            "metadata": metadata or {},
        })
        response = await self._exec(client.table(Tables.PROJECTS).insert(record))
        return self._first(response) or {}

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.PROJECTS).select("*").eq("id", project_id).limit(1)
        )
        return self._first(response)

    async def list_user_projects(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.PROJECTS)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        return self._all(response)

    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        client = self._require_client()
        updates = _strip_none({**updates, "updated_at": _now_iso()})
        response = await self._exec(
            client.table(Tables.PROJECTS).update(updates).eq("id", project_id)
        )
        return self._first(response) or {}

    async def delete_project(self, project_id: str) -> bool:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.PROJECTS).delete().eq("id", project_id)
        )
        return bool(self._all(response))

    # ─────────────────────────────────────────────────────────────────────────
    # Generations  (PRDs, roadmaps, architectures, etc.)
    # ─────────────────────────────────────────────────────────────────────────

    async def save_generation(
        self,
        generation_type: str,
        input_data: Dict[str, Any],
        output_content: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generic generation save — used by all AI-generation types."""
        client = self._require_client()
        record = _strip_none({
            "type": generation_type,
            "input_data": input_data,
            "output_content": output_content,
            "user_id": user_id,
            "project_id": project_id,
            "workflow_run_id": workflow_run_id,
            "metadata": metadata or {},
        })
        response = await self._exec(client.table(Tables.GENERATIONS).insert(record))
        return self._first(response) or {}

    async def save_prd(
        self,
        prd: Any,                                 # PRDOutput (Pydantic) or dict
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        workflow_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method for saving a structured PRD.

        Accepts either a Pydantic PRDOutput instance or a plain dict.
        Stores the JSON in `output_content` and also mirrors key fields
        (startup_summary, feature count, etc.) into `metadata` for easy querying.
        """
        # Normalise to dict
        if hasattr(prd, "model_dump"):
            prd_dict = prd.model_dump()
        elif isinstance(prd, dict):
            prd_dict = prd
        else:
            raise SupabaseServiceError(f"Unsupported PRD type: {type(prd).__name__}")

        # Build queryable metadata sidecar (only if the relevant keys are present)
        metadata: Dict[str, Any] = {}
        if "startup_summary" in prd_dict:
            metadata["startup_summary"] = prd_dict["startup_summary"]
        if isinstance(prd_dict.get("core_features"), list):
            metadata["feature_count"] = len(prd_dict["core_features"])
        tiers = (prd_dict.get("monetization_strategy") or {}).get("pricing_tiers")
        if isinstance(tiers, list):
            metadata["pricing_tier_count"] = len(tiers)

        return await self.save_generation(
            generation_type="prd",
            input_data=input_data or {},
            output_content=json.dumps(prd_dict, indent=2),
            user_id=user_id,
            project_id=project_id,
            workflow_run_id=workflow_run_id,
            metadata=metadata,
        )

    async def get_generation(self, generation_id: str) -> Optional[Dict[str, Any]]:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.GENERATIONS).select("*").eq("id", generation_id).limit(1)
        )
        return self._first(response)

    async def list_user_generations(
        self,
        user_id: str,
        generation_type: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        client = self._require_client()
        query = (
            client.table(Tables.GENERATIONS)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if generation_type:
            query = query.eq("type", generation_type)
        if project_id:
            query = query.eq("project_id", project_id)
        response = await self._exec(query)
        return self._all(response)

    async def list_project_generations(
        self,
        project_id: str,
        generation_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        client = self._require_client()
        query = (
            client.table(Tables.GENERATIONS)
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if generation_type:
            query = query.eq("type", generation_type)
        response = await self._exec(query)
        return self._all(response)

    # ─────────────────────────────────────────────────────────────────────────
    # Workflow runs
    # ─────────────────────────────────────────────────────────────────────────

    async def save_workflow_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        client = self._require_client()
        response = await self._exec(client.table(Tables.WORKFLOW_RUNS).insert(run_data))
        return self._first(response) or {}

    async def update_workflow_run(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.WORKFLOW_RUNS).update(updates).eq("id", run_id)
        )
        return self._first(response) or {}

    async def get_workflow_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        client = self._require_client()
        response = await self._exec(
            client.table(Tables.WORKFLOW_RUNS).select("*").eq("id", run_id).limit(1)
        )
        return self._first(response)

    # ─────────────────────────────────────────────────────────────────────────
    # Health
    # ─────────────────────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        """Lightweight connectivity check — returns True if the client can reach Supabase."""
        try:
            client = self._require_client()
            await self._exec(client.table(Tables.GENERATIONS).select("id").limit(1))
            return True
        except Exception as exc:
            logger.warning(f"Supabase ping failed: {exc}")
            return False


# ── Utility functions ────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_none(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys whose value is None so Supabase keeps existing/default values."""
    return {k: v for k, v in d.items() if v is not None}
