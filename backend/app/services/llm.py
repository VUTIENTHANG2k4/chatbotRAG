from __future__ import annotations

import os
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm(provider: str | None = None) -> BaseChatModel:
    """Return a LangChain chat model.

    provider: "ollama" (default) | "openai" | "gemini"
    """
    provider = (provider or settings.llm_provider).lower()

    if provider == "ollama":
        return _build_ollama()
    elif provider == "openai":
        return _build_openai()
    elif provider == "gemini":
        return _build_gemini()
    raise ValueError(f"Unknown LLM provider '{provider}'")


def clear_llm_cache() -> None:
    """Clear cached LLM instances (useful after changing model in .env)."""
    _build_ollama.cache_clear()
    _build_gemini.cache_clear()


@lru_cache(maxsize=1)
def _build_ollama() -> BaseChatModel:
    from langchain_ollama import ChatOllama

    logger.info("Initializing Ollama LLM: %s @ %s",
                settings.ollama_model, settings.ollama_base_url)
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
    )


def _build_openai() -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_api_key=api_key,
        temperature=0.0,
        streaming=True,
    )


@lru_cache(maxsize=1)
def _build_gemini() -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    logger.info("Initializing Gemini LLM: %s", settings.gemini_model)
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=api_key,
        temperature=0.0,
        streaming=True,
        # RAG answers must follow retrieved text; keep thinking shallow for latency.
        thinking_level="low",
    )


def check_ollama_health() -> bool:
    """Quick check if the Ollama server is reachable."""
    try:
        import httpx
        r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False
