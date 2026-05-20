from typing import Optional
from openai import AsyncOpenAI

from app.core.config import settings


class OpenAIService:
    def __init__(self, client: Optional[AsyncOpenAI]):
        self.client = client
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            raise RuntimeError(
                "OpenAI API key is not configured. "
                "Set the OPENAI_API_KEY environment variable."
            )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.choices[0].message.content or ""

    async def generate_prd(
        self,
        idea_title: str,
        description: str,
        target_market: str,
        problem_statement: str,
    ) -> str:
        system_prompt = (
            "You are a senior product manager and startup advisor. "
            "Generate a comprehensive, professional Product Requirements Document (PRD) "
            "for the given startup idea. Structure it with: Executive Summary, Problem Statement, "
            "Goals & Success Metrics, User Personas, Feature Requirements (P0/P1/P2), "
            "Technical Constraints, Timeline, and Open Questions. "
            "Be specific, actionable, and startup-focused."
        )
        user_prompt = (
            f"Startup Idea: {idea_title}\n"
            f"Description: {description}\n"
            f"Target Market: {target_market}\n"
            f"Problem Statement: {problem_statement}\n\n"
            "Generate a detailed PRD in Markdown format."
        )
        return await self.generate(system_prompt, user_prompt)

    async def generate_roadmap(
        self,
        idea_title: str,
        description: str,
        timeline_months: int,
        team_size: int,
    ) -> str:
        system_prompt = (
            "You are a seasoned CTO and startup execution expert. "
            "Generate a practical, milestone-driven product roadmap. "
            "Organize by phases (MVP, Growth, Scale), include key milestones, "
            "resource requirements, and risk flags per phase. "
            "Be realistic about timelines and what a small team can achieve."
        )
        user_prompt = (
            f"Product: {idea_title}\n"
            f"Description: {description}\n"
            f"Timeline: {timeline_months} months\n"
            f"Team Size: {team_size} people\n\n"
            "Generate a detailed product roadmap in Markdown format with phases, milestones, and deliverables."
        )
        return await self.generate(system_prompt, user_prompt)

    async def generate_architecture(
        self,
        idea_title: str,
        description: str,
        tech_preferences: str,
        scale_requirements: str,
    ) -> str:
        system_prompt = (
            "You are a principal software architect specializing in scalable SaaS systems. "
            "Design a production-ready system architecture for the given startup. "
            "Include: System Overview, Component Diagram (described in text), "
            "Technology Stack with justifications, Data Models, API Design patterns, "
            "Infrastructure & Deployment strategy, Security considerations, "
            "and Scaling strategy. Be opinionated and practical."
        )
        user_prompt = (
            f"Product: {idea_title}\n"
            f"Description: {description}\n"
            f"Tech Preferences: {tech_preferences}\n"
            f"Scale Requirements: {scale_requirements}\n\n"
            "Generate a detailed system architecture document in Markdown format."
        )
        return await self.generate(system_prompt, user_prompt)
