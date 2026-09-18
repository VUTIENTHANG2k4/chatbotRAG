from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, documents, health
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def _startup_ingest() -> None:
    """Background thread: scan data_dir recursively and ingest new files on startup."""
    import time
    time.sleep(3)  # wait for server to be fully ready

    from app.services.ingestion import ingest_all
    try:
        results = ingest_all(overwrite=False)
        ok = [r for r in results if r["status"] == "success"]
        skipped = [r for r in results if r["status"] == "skipped"]
        errors = [r for r in results if r["status"] == "error"]
        if results:
            logger.info(
                "Startup auto-ingest: %d indexed, %d skipped, %d errors",
                len(ok), len(skipped), len(errors),
            )
        for r in ok:
            logger.info("  ✔ %s (%d chunks)", r["source"], r.get("chunks", 0))
        for r in errors:
            logger.warning("  ✖ %s — %s", r["source"], r.get("reason", "unknown"))
    except Exception:
        logger.exception("Startup auto-ingest failed unexpectedly")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("LLM provider: %s | Embedding provider: %s",
                settings.llm_provider, settings.embed_provider)
    settings.ensure_dirs()
    # Auto-ingest any files already placed in data/ (runs in background, non-blocking)
    threading.Thread(target=_startup_ingest, daemon=True, name="startup-ingest").start()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for the Vietnamese Legal-Document RAG system.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }
