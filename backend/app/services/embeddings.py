from __future__ import annotations

from functools import lru_cache
from typing import List

from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_embedding_model(provider: str | None = None) -> Embeddings:
    """Return a LangChain Embeddings instance.

    provider: "huggingface" (default) | "openai"
    """
    provider = (provider or settings.embed_provider).lower()

    if provider in ("huggingface", "hf"):
        return _get_hf_embeddings()
    elif provider == "openai":
        return _get_openai_embeddings()
    raise ValueError(f"Unknown embedding provider '{provider}'")


@lru_cache(maxsize=1)
def _get_hf_embeddings() -> Embeddings:
    from langchain_huggingface import HuggingFaceEmbeddings

    logger.info("Loading HuggingFace embedding model: %s", settings.hf_embed_model)
    return HuggingFaceEmbeddings(
        model_name=settings.hf_embed_model,
        model_kwargs={"device": settings.hf_device},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def _get_openai_embeddings() -> Embeddings:
    import os
    from langchain_openai import OpenAIEmbeddings

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)


def embed_texts(texts: List[str], provider: str | None = None) -> List[List[float]]:
    return get_embedding_model(provider).embed_documents(texts)


def embed_query(query: str, provider: str | None = None) -> List[float]:
    return get_embedding_model(provider).embed_query(query)


def get_embedding_dim(provider: str | None = None) -> int:
    """Return the dimensionality of the configured embedding model."""
    sample = embed_query("test", provider)
    return len(sample)
