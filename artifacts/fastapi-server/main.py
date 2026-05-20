import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import health, prd, roadmap, architecture


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"FounderOS AI API starting on port {settings.PORT}")
    yield
    print("FounderOS AI API shutting down")


app = FastAPI(
    title="FounderOS AI API",
    description="AI-powered startup execution platform — generate PRDs, roadmaps, and architecture plans.",
    version="1.0.0",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/v1")
app.include_router(prd.router, prefix="/v1")
app.include_router(roadmap.router, prefix="/v1")
app.include_router(architecture.router, prefix="/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
