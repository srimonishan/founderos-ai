from fastapi import APIRouter

from app.api.v1.endpoints import generations, workflows, health

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(generations.router)
api_router.include_router(workflows.router)
