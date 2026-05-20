"""
OpenAI Service
==============
Async wrapper around the OpenAI Python SDK (v1+).

Features:
  * Async-first: all calls use `AsyncOpenAI`
  * Environment-driven configuration via `app.core.config.settings`
  * Structured JSON outputs via `response_format={"type": "json_object"}`
  * Automatic fallback model on primary failure
  * Clean, typed error handling with custom exceptions

Public surface:
  * OpenAIService.generate_prd(startup_idea, target_audience, industry) -> PRDOutput
  * OpenAIService.generate_roadmap(...) -> str          (used by workflows)
  * OpenAIService.generate_architecture(...) -> str     (used by workflows)
  * OpenAIService.complete(...)                         (raw text completion)
  * OpenAIService.complete_json(...)                    (raw structured JSON completion)
"""

import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.models.generation import PRDOutput

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ── Exceptions ────────────────────────────────────────────────────────────────

class OpenAIServiceError(Exception):
    """Base error for the OpenAI service."""


class OpenAINotConfiguredError(OpenAIServiceError):
    """Raised when OPENAI_API_KEY is missing."""


class OpenAIInvalidResponseError(OpenAIServiceError):
    """Raised when the model returns a malformed structured response."""


# ── Service ───────────────────────────────────────────────────────────────────

class OpenAIService:
    """Async service for interacting with OpenAI's Chat Completions API."""

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        from app.core.dependencies import get_openai_client

        self.client = client or get_openai_client()
        self.model = settings.OPENAI_MODEL
        self.fallback_model = settings.OPENAI_FALLBACK_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _require_client(self) -> AsyncOpenAI:
        if not self.client:
            raise OpenAINotConfiguredError(
                "OPENAI_API_KEY is not configured. Set it in your environment or .env file."
            )
        return self.client

    async def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> str:
        client = self._require_client()
        chosen_model = model or self.model

        kwargs: Dict[str, Any] = {
            "model": chosen_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""

        except (APITimeoutError, RateLimitError, APIError) as exc:
            # Retry once with fallback model
            if chosen_model != self.fallback_model:
                logger.warning(
                    f"OpenAI call failed on {chosen_model} ({exc.__class__.__name__}). "
                    f"Retrying with fallback {self.fallback_model}."
                )
                kwargs["model"] = self.fallback_model
                response = await client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            logger.error(f"OpenAI fallback model also failed: {exc}")
            raise OpenAIServiceError(f"OpenAI request failed: {exc}") from exc

    # ── Public — raw text ─────────────────────────────────────────────────────

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Free-form text completion."""
        return await self._chat(
            system_prompt, user_prompt,
            model=model, max_tokens=max_tokens, temperature=temperature,
        )

    # ── Public — structured JSON ──────────────────────────────────────────────

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        *,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """
        Structured completion. Forces JSON mode and validates against a Pydantic schema.
        Returns a validated instance of `schema`.
        """
        # Inject schema hint so the model knows the expected shape
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        augmented_system = (
            f"{system_prompt}\n\n"
            f"Respond with ONLY a valid JSON object matching this schema:\n{schema_json}\n"
            f"Do not include markdown code fences or any prose outside the JSON object."
        )

        raw = await self._chat(
            augmented_system, user_prompt,
            model=model, max_tokens=max_tokens, temperature=temperature,
            json_mode=True,
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(f"Model returned invalid JSON: {raw[:200]!r}")
            raise OpenAIInvalidResponseError(f"Model returned invalid JSON: {exc}") from exc

        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            logger.error(f"JSON did not match schema: {exc}")
            raise OpenAIInvalidResponseError(
                f"Model output failed schema validation: {exc}"
            ) from exc

    # ── Public — high-level generation helpers ────────────────────────────────

    async def generate_prd(
        self,
        startup_idea: str,
        target_audience: str,
        industry: str,
    ) -> PRDOutput:
        """
        Generate a structured Product Requirements Document.

        Args:
            startup_idea: One-paragraph description of the startup idea.
            target_audience: Who the product is for.
            industry: The industry / vertical the startup operates in.

        Returns:
            PRDOutput with:
              - startup_summary: 2-3 sentence executive summary
              - core_features: list of {name, description, priority}
              - monetization_strategy: revenue model description + pricing tiers
              - roadmap_overview: list of {phase, timeline, milestones}
        """
        system_prompt = (
            "You are a senior product manager and startup strategist with 15+ years of "
            "experience launching successful SaaS products. Generate a concise but "
            "comprehensive Product Requirements Document for the given startup idea. "
            "Be specific, actionable, and realistic. Tailor the language to the industry."
        )

        user_prompt = (
            f"Startup Idea:\n{startup_idea}\n\n"
            f"Target Audience:\n{target_audience}\n\n"
            f"Industry:\n{industry}\n\n"
            "Generate the PRD. Include:\n"
            "  - startup_summary: 2-3 sentences capturing the vision and value prop\n"
            "  - core_features: 4-7 features, each with name, 1-2 sentence description, "
            "and priority (P0 | P1 | P2)\n"
            "  - monetization_strategy: revenue model + at least 2 pricing tiers with "
            "price_usd_per_month and target_segment\n"
            "  - roadmap_overview: 3-4 phases (e.g. MVP / Beta / Launch / Scale) with "
            "timeline (e.g. 'Months 1-3') and 2-4 key milestones each"
        )

        logger.info(f"Generating structured PRD for industry='{industry}'")

        return await self.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=PRDOutput,
        )

    async def generate_roadmap(
        self,
        idea_title: str,
        description: str,
        timeline_months: int,
        team_size: int,
    ) -> str:
        """Markdown roadmap — used by the multi-step startup_analysis workflow."""
        return await self.complete(
            system_prompt=(
                "You are a seasoned CTO and startup execution expert. "
                "Generate a practical, milestone-driven product roadmap organised by phases "
                "(MVP → Growth → Scale). Include key milestones, resource requirements, "
                "and risk flags. Be realistic about what a small team can achieve."
            ),
            user_prompt=(
                f"Product: {idea_title}\n"
                f"Description: {description}\n"
                f"Timeline: {timeline_months} months\n"
                f"Team Size: {team_size} people\n\n"
                "Generate a detailed roadmap in Markdown format."
            ),
        )

    async def generate_architecture(
        self,
        idea_title: str,
        description: str,
        tech_preferences: str,
        scale_requirements: str,
    ) -> str:
        """Markdown system architecture — used by the multi-step startup_analysis workflow."""
        return await self.complete(
            system_prompt=(
                "You are a principal software architect specialising in scalable SaaS systems. "
                "Design a production-ready system architecture covering: System Overview, "
                "Component breakdown, Technology Stack with justifications, Data Models, "
                "API Design patterns, Infrastructure & Deployment, Security, Scaling strategy."
            ),
            user_prompt=(
                f"Product: {idea_title}\n"
                f"Description: {description}\n"
                f"Tech Preferences: {tech_preferences}\n"
                f"Scale Requirements: {scale_requirements}\n\n"
                "Generate a detailed architecture document in Markdown format."
            ),
        )
