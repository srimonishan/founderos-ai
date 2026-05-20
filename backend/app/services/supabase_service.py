import logging
from typing import Any, Dict, List, Optional

from supabase import Client

from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    def __init__(self, client: Optional[Client] = None):
        from app.core.dependencies import get_supabase_client
        self.client = client or get_supabase_client()

    def _require_client(self) -> Client:
        if not self.client:
            raise RuntimeError(
                "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
            )
        return self.client

    async def save_generation(
        self,
        generation_type: str,
        input_data: Dict[str, Any],
        output_content: str,
        user_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = self._require_client()
        record = {
            "type": generation_type,
            "input_data": input_data,
            "output_content": output_content,
            "user_id": user_id,
            "workflow_run_id": workflow_run_id,
        }
        response = client.table("generations").insert(record).execute()
        return response.data[0] if response.data else {}

    async def get_generation(self, generation_id: str) -> Optional[Dict[str, Any]]:
        client = self._require_client()
        response = (
            client.table("generations")
            .select("*")
            .eq("id", generation_id)
            .single()
            .execute()
        )
        return response.data

    async def list_user_generations(
        self,
        user_id: str,
        generation_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        client = self._require_client()
        query = (
            client.table("generations")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        if generation_type:
            query = query.eq("type", generation_type)
        response = query.execute()
        return response.data or []

    async def save_workflow_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        client = self._require_client()
        response = client.table("workflow_runs").insert(run_data).execute()
        return response.data[0] if response.data else {}

    async def update_workflow_run(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        client = self._require_client()
        response = (
            client.table("workflow_runs")
            .update(updates)
            .eq("id", run_id)
            .execute()
        )
        return response.data[0] if response.data else {}
