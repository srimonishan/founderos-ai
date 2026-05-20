"""
Authentication dependencies
===========================
Lightweight user-identity extraction for FastAPI routes.

Strategy:
  * Read the Supabase JWT from the `Authorization: Bearer <token>` header
  * Decode it (without re-verifying the signature here — Supabase already
    validated it on the frontend; for server-side verification, plug in the
    Supabase JWKS or `auth.get_user(jwt)` if you need stronger guarantees)
  * Also accept an `X-User-Id` header as a convenience for server-to-server
    calls during development

Two dependencies are exposed:

  * `get_current_user_id` — returns `None` if no auth is present
  * `require_user_id`     — raises 401 if no auth is present
"""

import base64
import json
import logging
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


def _decode_jwt_subject(token: str) -> Optional[str]:
    """
    Decode (NOT verify) a JWT and return its `sub` claim.

    We trust Supabase's frontend SDK to have verified the token; this is
    only extracting the user id for persistence/logging purposes.
    """
    try:
        _, payload_b64, _ = token.split(".")
        # Base64URL → base64 with padding
        padding = "=" * (-len(payload_b64) % 4)
        payload = base64.urlsafe_b64decode(payload_b64 + padding)
        claims = json.loads(payload)
        return claims.get("sub")
    except Exception as exc:
        logger.debug(f"Could not decode JWT: {exc}")
        return None


async def get_current_user_id(
    authorization: Optional[str] = Header(default=None),
    x_user_id: Optional[str] = Header(default=None),
) -> Optional[str]:
    """
    Best-effort user extraction. Returns None if no auth context is present.

    Order of precedence:
      1. `Authorization: Bearer <supabase-jwt>` → decoded `sub` claim
      2. `X-User-Id: <uuid>` header (dev / server-to-server)
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        user_id = _decode_jwt_subject(token)
        if user_id:
            return user_id

    if x_user_id:
        return x_user_id.strip()

    return None


async def require_user_id(
    authorization: Optional[str] = Header(default=None),
    x_user_id: Optional[str] = Header(default=None),
) -> str:
    """Like `get_current_user_id` but raises 401 if no user can be resolved."""
    user_id = await get_current_user_id(authorization=authorization, x_user_id=x_user_id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthenticated",
                "message": "Authentication required. Provide a Supabase Bearer token "
                           "or X-User-Id header.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
