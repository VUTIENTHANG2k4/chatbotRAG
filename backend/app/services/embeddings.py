from __future__ import annotations

from functools import lru_cache
from typing import List

from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_embedding_model(provider: str | None = None) -> Embeddings:
    """Return a LangChain Embeddings instance.

    provider: "huggingface" (local) | "hf-inference" (same model, remote) | "openai"
    """
    provider = (provider or settings.embed_provider).lower()

    if provider in ("huggingface", "hf"):
        return _get_hf_embeddings()
    if provider in ("hf-inference", "huggingface-api"):
        return _get_hf_inference_embeddings()
    if provider == "openai":
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


class HuggingFaceInferenceEmbeddings(Embeddings):
    """Call keepitreal/vietnamese-sbert on Hugging Face Inference.

    Vectors stay 768-d and L2-normalized, matching the local index in Qdrant.
    """

    def __init__(self, model: str, token: str) -> None:
        self._model = model
        self._token = token

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self._token:
            raise ValueError(
                "HF_TOKEN chưa được đặt. Tạo token đọc tại huggingface.co/settings/tokens."
            )
        from huggingface_hub import InferenceClient

        raw = InferenceClient(api_key=self._token).feature_extraction(
            texts,
            model=self._model,
            normalize=True,
        )
        return _coerce_sentence_vectors(raw, len(texts))

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


def _coerce_sentence_vectors(raw: object, count: int) -> List[List[float]]:
    """Accept a sentence matrix or token tensor and return L2-normalized rows."""
    import numpy as np

    arr = np.asarray(raw, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    elif arr.ndim == 3:
        arr = arr.mean(axis=1)
    elif arr.ndim == 2 and count == 1 and arr.shape[0] != 1:
        arr = arr.mean(axis=0, keepdims=True)
    if arr.ndim != 2 or arr.shape[0] != count:
        raise ValueError(f"Unexpected embedding shape {getattr(arr, 'shape', None)} for {count} texts")
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return (arr / norms).astype(np.float32).tolist()


@lru_cache(maxsize=1)
def _get_hf_inference_embeddings() -> Embeddings:
    logger.info("Using Hugging Face Inference embeddings: %s", settings.hf_embed_model)
    return HuggingFaceInferenceEmbeddings(
        model=settings.hf_embed_model,
        token=settings.hf_token,
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
