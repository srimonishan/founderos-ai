from typing import Optional, Any, Dict, List
from supabase import Client

from app.core.config import settings


class SupabaseService:
    def __init__(self, client: Optional[Client]):
        self.client = client

    def _require_client(self):
        if not self.client:
            raise RuntimeError(
                "Supabase is not configured. "
                "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            )

    async def save_generation(
        self,
        generation_type: str,
        input_data: Dict[str, Any],
        output_content: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._require_client()

        record = {
            "type": generation_type,
            "input_data": input_data,
            "output_content": output_content,
            "user_id": user_id,
        }

        response = self.client.table("generations").insert(record).execute()
        return response.data[0] if response.data else {}

    async def get_user_generations(
        self,
        user_id: str,
        generation_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        self._require_client()

        query = (
            self.client.table("generations")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
        )

        if generation_type:
            query = query.eq("type", generation_type)

        response = query.execute()
        return response.data or []

    async def get_generation_by_id(self, generation_id: str) -> Optional[Dict[str, Any]]:
        self._require_client()

        response = (
            self.client.table("generations")
            .select("*")
            .eq("id", generation_id)
            .single()
            .execute()
        )
        return response.data
