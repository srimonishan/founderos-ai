from functools import lru_cache
from typing import Optional

from openai import AsyncOpenAI
from supabase import create_client, Client

from app.core.config import settings


@lru_cache(maxsize=1)
def get_openai_client() -> Optional[AsyncOpenAI]:
    if not settings.is_openai_configured:
        return None
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@lru_cache(maxsize=1)
def get_supabase_client() -> Optional[Client]:
    if not settings.is_supabase_configured:
        return None
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    return create_client(settings.SUPABASE_URL, key)


def require_openai() -> AsyncOpenAI:
    client = get_openai_client()
    if client is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI is not configured. Set the OPENAI_API_KEY environment variable.",
        )
    return client


def require_supabase() -> Client:
    client = get_supabase_client()
    if client is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.",
        )
    return client
