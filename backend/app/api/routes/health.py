from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.chat import HealthResponse
from app.services.llm import check_ollama_health
from app.services.vectorstore import get_collection_stats

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    stats = get_collection_stats()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_version=settings.app_version,
        llm_provider=settings.llm_provider,
        embed_provider=settings.embed_provider,
        total_chunks=stats["total_chunks"],
    )


@router.get("/health/llm")
async def health_llm() -> dict:
    """Check connectivity to the configured LLM backend (Ollama)."""
    if settings.llm_provider == "ollama":
        return {
            "provider": "ollama",
            "model": settings.ollama_model,
            "base_url": settings.ollama_base_url,
            "reachable": check_ollama_health(),
        }
    return {"provider": settings.llm_provider, "reachable": True}
