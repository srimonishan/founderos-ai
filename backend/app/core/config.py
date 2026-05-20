"""
Configuration & Environment Variable Loading
=============================================
Centralised, type-safe configuration for the FounderOS AI backend.

Loading order (highest priority first):
  1. Real process environment variables (set by Replit Secrets, CI, Docker, etc.)
  2. Values from a local `.env` file (only used for local development)
  3. Defaults declared on the Settings class below

The `.env` file is loaded via `python-dotenv` and is gitignored.
NEVER commit a real `.env` — use `.env.example` as the template.
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.cors import CORSConfig, build_cors_config


# ── .env loading ──────────────────────────────────────────────────────────────
# Resolve project paths so this works no matter the current working directory.
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # backend/
PROJECT_ROOT = BASE_DIR.parent                              # repo root
ENV_FILE = BASE_DIR / ".env"

# Load `.env` if it exists. `override=False` means process env vars (Replit
# Secrets, container env, CI variables) always win over the file.
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=False)


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    """
    Application settings. All values can be overridden via environment variables.

    Usage:
        from app.core.config import settings
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        validate_default=True,
    )

    # ── App metadata ──────────────────────────────────────────────────────────
    APP_NAME: str = "FounderOS AI"
    APP_VERSION: str = "1.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    SECRET_KEY: str = "change-me-in-production"

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Concrete origin allow-list (auto-populated in `model_post_init`).
    CORS_ORIGINS: List[str] = []
    # Production primary frontend URL (e.g. https://app.founderos.ai).
    FRONTEND_URL: str = ""

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_FALLBACK_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = Field(default=4096, ge=256, le=16384)
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    # Accept both SUPABASE_SERVICE_KEY (canonical) and SUPABASE_SERVICE_ROLE_KEY (legacy)
    SUPABASE_SERVICE_KEY: str = Field(
        default="",
        validation_alias="SUPABASE_SERVICE_KEY",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = ""   # legacy alias, populated from env if set

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def model_post_init(self, __context) -> None:
        # Auto-build the resolved CORS config (origins + regex) on startup
        cors = build_cors_config(
            environment=self.ENVIRONMENT,
            frontend_url=self.FRONTEND_URL or None,
            extra_origins=self.CORS_ORIGINS or None,
        )
        object.__setattr__(self, "_cors_config", cors)
        object.__setattr__(self, "CORS_ORIGINS", cors.allow_origins)

        # Reconcile the two Supabase service-key names so callers can use either
        if not self.SUPABASE_SERVICE_KEY and self.SUPABASE_SERVICE_ROLE_KEY:
            object.__setattr__(self, "SUPABASE_SERVICE_KEY", self.SUPABASE_SERVICE_ROLE_KEY)
        if not self.SUPABASE_SERVICE_ROLE_KEY and self.SUPABASE_SERVICE_KEY:
            object.__setattr__(self, "SUPABASE_SERVICE_ROLE_KEY", self.SUPABASE_SERVICE_KEY)

    @property
    def cors(self) -> CORSConfig:
        """Resolved CORS configuration. Built once in `model_post_init`."""
        return self._cors_config

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def _validate_openai_key_format(cls, v: str) -> str:
        if v and not (v.startswith("sk-") or v.startswith("sk_")):
            # Only warn — don't reject; users may use proxies
            pass
        return v

    @field_validator("SUPABASE_URL")
    @classmethod
    def _validate_supabase_url(cls, v: str) -> str:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("SUPABASE_URL must start with http:// or https://")
        return v.rstrip("/") if v else v

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def is_openai_configured(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_ANON_KEY)

    @property
    def has_supabase_service_key(self) -> bool:
        return bool(self.SUPABASE_SERVICE_KEY)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production

    def safe_summary(self) -> dict:
        """Return non-sensitive config for logging or /health/info."""
        return {
            "app_name": self.APP_NAME,
            "version": self.APP_VERSION,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "port": self.PORT,
            "openai_configured": self.is_openai_configured,
            "openai_model": self.OPENAI_MODEL,
            "supabase_configured": self.is_supabase_configured,
            "supabase_service_key_configured": self.has_supabase_service_key,
            "cors": self.cors.summary(),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
# Imported as `from app.core.config import settings`
settings = Settings()
