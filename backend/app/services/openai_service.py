import logging
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self, client: Optional[AsyncOpenAI] = None):
        from app.core.dependencies import get_openai_client
        self.client = client or get_openai_client()
        self.model = settings.OPENAI_MODEL
        self.fallback_model = settings.OPENAI_FALLBACK_MODEL

    def _require_client(self) -> AsyncOpenAI:
        if not self.client:
            raise RuntimeError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )
        return self.client

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        client = self._require_client()
        chosen_model = model or self.model

        logger.debug(f"OpenAI request — model={chosen_model}, prompt_len={len(user_prompt)}")

        try:
            response = await client.chat.completions.create(
                model=chosen_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
                temperature=temperature if temperature is not None else settings.OPENAI_TEMPERATURE,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            # Retry with fallback model if primary fails
            if chosen_model != self.fallback_model:
                logger.warning(f"Primary model failed ({exc}), retrying with {self.fallback_model}")
                response = await client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
                    temperature=temperature if temperature is not None else settings.OPENAI_TEMPERATURE,
                )
                return response.choices[0].message.content or ""
            raise

    async def generate_prd(self, idea_title: str, description: str, target_market: str, problem_statement: str) -> str:
        return await self.complete(
            system_prompt=(
                "You are a senior product manager and startup advisor. "
                "Generate a comprehensive, professional Product Requirements Document (PRD). "
                "Structure it with: Executive Summary, Problem Statement, Goals & Success Metrics, "
                "User Personas, Feature Requirements (P0/P1/P2), Technical Constraints, "
                "Timeline, and Open Questions. Be specific, actionable, and startup-focused."
            ),
            user_prompt=(
                f"Startup Idea: {idea_title}\n"
                f"Description: {description}\n"
                f"Target Market: {target_market}\n"
                f"Problem Statement: {problem_statement}\n\n"
                "Generate a detailed PRD in Markdown format."
            ),
        )

    async def generate_roadmap(self, idea_title: str, description: str, timeline_months: int, team_size: int) -> str:
        return await self.complete(
            system_prompt=(
                "You are a seasoned CTO and startup execution expert. "
                "Generate a practical, milestone-driven product roadmap organised by phases "
                "(MVP → Growth → Scale). Include key milestones, resource requirements, and risk flags. "
                "Be realistic about what a small team can achieve."
            ),
            user_prompt=(
                f"Product: {idea_title}\n"
                f"Description: {description}\n"
                f"Timeline: {timeline_months} months\n"
                f"Team Size: {team_size} people\n\n"
                "Generate a detailed roadmap in Markdown format with phases, milestones, and deliverables."
            ),
        )

    async def generate_architecture(self, idea_title: str, description: str, tech_preferences: str, scale_requirements: str) -> str:
        return await self.complete(
            system_prompt=(
                "You are a principal software architect specialising in scalable SaaS systems. "
                "Design a production-ready system architecture. Include: System Overview, "
                "Component breakdown, Technology Stack with justifications, Data Models, "
                "API Design patterns, Infrastructure & Deployment, Security, and Scaling strategy."
            ),
            user_prompt=(
                f"Product: {idea_title}\n"
                f"Description: {description}\n"
                f"Tech Preferences: {tech_preferences}\n"
                f"Scale Requirements: {scale_requirements}\n\n"
                "Generate a detailed architecture document in Markdown format."
            ),
        )
