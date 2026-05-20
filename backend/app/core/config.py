import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


def _build_cors_origins() -> List[str]:
    """
    Build the allowed CORS origin list from environment at import time.

    Always includes:
      - http/https localhost on common dev ports
      - Any REPLIT_DOMAINS entry (comma-separated, injected by the platform)
      - Any EXTRA_CORS_ORIGINS override from the environment
    """
    origins: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://localhost:19291",
        "https://localhost",
        "https://localhost:3000",
        "https://localhost:5173",
    ]

    # Replit injects REPLIT_DOMAINS as a comma-separated list of public domains
    replit_domains = os.environ.get("REPLIT_DOMAINS", "")
    for domain in replit_domains.split(","):
        domain = domain.strip()
        if domain:
            origins.append(f"https://{domain}")
            origins.append(f"http://{domain}")

    # Legacy single-domain variable
    replit_dev_domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
    if replit_dev_domain:
        origins.append(f"https://{replit_dev_domain}")

    # Wildcard Replit subdomains via regex-style catch-all
    origins.append("https://*.replit.dev")
    origins.append("https://*.replit.app")
    origins.append("https://*.repl.co")

    # Allow additional origins via env override
    extra = os.environ.get("EXTRA_CORS_ORIGINS", "")
    for origin in extra.split(","):
        origin = origin.strip()
        if origin:
            origins.append(origin)

    return list(dict.fromkeys(origins))  # deduplicate, preserve order


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "FounderOS AI"
    APP_VERSION: str = "1.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production
    SECRET_KEY: str = "change-me-in-production"

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Computed at startup — override per-environment via EXTRA_CORS_ORIGINS
    CORS_ORIGINS: List[str] = []

    def model_post_init(self, __context) -> None:
        # Populate CORS_ORIGINS after settings are loaded
        if not self.CORS_ORIGINS:
            object.__setattr__(self, "CORS_ORIGINS", _build_cors_origins())

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_FALLBACK_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def is_openai_configured(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_ANON_KEY)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production


settings = Settings()
