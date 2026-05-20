"""
CORS Configuration
==================
Production-ready CORS setup for FounderOS AI.

Supports:
  * Local development (localhost on all common dev ports)
  * Replit dev preview (`*.replit.dev`, `*.replit.app`, `*.repl.co`)
  * Replit production domains (from `REPLIT_DOMAINS`)
  * Vercel previews & production (`*.vercel.app`, custom prod via env)
  * Custom additional origins (via `EXTRA_CORS_ORIGINS`, comma-separated)
  * Production frontend URL (via `FRONTEND_URL`)

Security posture:
  * **No wildcard `*` origin** — every accepted origin matches either a
    concrete entry in the allow-list or a tightly-scoped regex.
  * Credentials are allowed only because the allow-list is explicit.
  * Allowed methods and headers are enumerated, not wildcarded.
  * In production, localhost origins are dropped automatically.

Environment overrides:
  * `FRONTEND_URL`         — primary production frontend (e.g. https://app.example.com)
  * `EXTRA_CORS_ORIGINS`   — comma-separated extra origins
  * `CORS_ALLOW_VERCEL`    — "true"/"false" (default: true). Enables *.vercel.app regex.
  * `CORS_ALLOW_REPLIT`    — "true"/"false" (default: true). Enables Replit regex.
  * `REPLIT_DOMAINS`       — auto-populated by Replit
  * `REPLIT_DEV_DOMAIN`    — auto-populated by Replit
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────────────────────────────────────

_LOCALHOST_ORIGINS: List[str] = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:4173",   # Vite preview
    "http://localhost:5000",
    "http://localhost:5173",   # Vite dev
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:19006",  # Expo
    "http://localhost:19291",  # founder-os dev port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "https://localhost",
    "https://localhost:3000",
    "https://localhost:5173",
]

# Tightly-scoped allow-list of HTTPS suffixes we trust to host the frontend
_ALLOWED_HOST_SUFFIXES = {
    "replit": (r"replit\.dev", r"replit\.app", r"repl\.co"),
    "vercel": (r"vercel\.app",),
}

_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Accept-Language",
    "Origin",
    "X-Request-ID",
    "X-User-Id",
    "X-Requested-With",
]
_EXPOSE_HEADERS = ["X-Request-ID", "X-Response-Time"]
_PREFLIGHT_MAX_AGE = 600  # seconds


# ── Result type ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CORSConfig:
    """Fully-resolved CORS configuration passed to CORSMiddleware."""
    allow_origins: List[str]
    allow_origin_regex: Optional[str]
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: list(_ALLOWED_METHODS))
    allow_headers: List[str] = field(default_factory=lambda: list(_ALLOWED_HEADERS))
    expose_headers: List[str] = field(default_factory=lambda: list(_EXPOSE_HEADERS))
    max_age: int = _PREFLIGHT_MAX_AGE

    def summary(self) -> dict:
        """Non-sensitive summary for /health/info and logs."""
        return {
            "origin_count": len(self.allow_origins),
            "has_regex": bool(self.allow_origin_regex),
            "regex": self.allow_origin_regex,
            "allow_credentials": self.allow_credentials,
            "methods": self.allow_methods,
        }


# ── Builder ──────────────────────────────────────────────────────────────────

def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str) -> List[str]:
    return [v.strip().rstrip("/") for v in value.split(",") if v.strip()]


def build_cors_config(
    *,
    environment: str = "development",
    frontend_url: Optional[str] = None,
    extra_origins: Optional[List[str]] = None,
) -> CORSConfig:
    """
    Build a production-ready CORSConfig from env vars + explicit overrides.

    Args:
        environment: "development" | "staging" | "production"
        frontend_url: optional explicit primary frontend URL
        extra_origins: optional extra concrete origins
    """
    is_prod = environment == "production"
    origins: List[str] = []

    # 1. Localhost — only in non-production environments
    if not is_prod:
        origins.extend(_LOCALHOST_ORIGINS)

    # 2. Replit prod domains (from REPLIT_DOMAINS, comma-separated)
    for domain in _split_csv(os.environ.get("REPLIT_DOMAINS", "")):
        origins.append(f"https://{domain}")
        if not is_prod:
            origins.append(f"http://{domain}")

    # 3. Replit dev workspace domain (single value)
    dev_domain = os.environ.get("REPLIT_DEV_DOMAIN", "").strip().rstrip("/")
    if dev_domain:
        origins.append(f"https://{dev_domain}")

    # 4. Primary production frontend
    fe_url = (frontend_url or os.environ.get("FRONTEND_URL", "")).strip().rstrip("/")
    if fe_url:
        origins.append(fe_url)

    # 5. Extra origins from env + explicit args
    origins.extend(_split_csv(os.environ.get("EXTRA_CORS_ORIGINS", "")))
    if extra_origins:
        origins.extend(o.rstrip("/") for o in extra_origins if o)

    # Dedupe while preserving order
    origins = list(dict.fromkeys(origins))

    # 6. Build the regex for trusted hosting suffixes
    regex_parts: List[str] = []
    if _env_bool("CORS_ALLOW_REPLIT", default=True):
        regex_parts.extend(_ALLOWED_HOST_SUFFIXES["replit"])
    if _env_bool("CORS_ALLOW_VERCEL", default=True):
        regex_parts.extend(_ALLOWED_HOST_SUFFIXES["vercel"])

    regex = (
        rf"^https://([a-zA-Z0-9-]+\.)*({'|'.join(regex_parts)})$"
        if regex_parts else None
    )

    logger.info(
        f"CORS configured (env={environment}): "
        f"{len(origins)} explicit origin(s), regex={'on' if regex else 'off'}"
    )

    return CORSConfig(
        allow_origins=origins,
        allow_origin_regex=regex,
    )
