from __future__ import annotations

import pickle
import threading
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.text import simple_tokenize

logger = get_logger(__name__)

_INDEX_FILE = settings.bm25_index_path / "bm25_index.pkl"
_CORPUS_FILE = settings.bm25_index_path / "bm25_corpus.pkl"

# Lock to prevent concurrent rebuilds
_lock = threading.Lock()

# With remote Qdrant the instance is stateless: corpus and index live in memory
# and are rebuilt from Qdrant payloads (see rebuild_from_vectorstore).
_mem_corpus: List[Document] = []
_mem_index: Any = None


def _load_corpus() -> List[Document]:
    if settings.use_remote_qdrant:
        return _mem_corpus
    if _CORPUS_FILE.exists():
        with open(_CORPUS_FILE, "rb") as f:
            return pickle.load(f)
    return []


def _save_corpus(corpus: List[Document]) -> None:
    settings.bm25_index_path.mkdir(parents=True, exist_ok=True)
    with open(_CORPUS_FILE, "wb") as f:
        pickle.dump(corpus, f)


def _load_index():
    if settings.use_remote_qdrant:
        return _mem_index
    if _INDEX_FILE.exists():
        with open(_INDEX_FILE, "rb") as f:
            return pickle.load(f)
    return None


def _save_index(index) -> None:
    settings.bm25_index_path.mkdir(parents=True, exist_ok=True)
    with open(_INDEX_FILE, "wb") as f:
        pickle.dump(index, f)


def build_index(corpus: List[Document]) -> None:
    global _mem_corpus, _mem_index
    from rank_bm25 import BM25Okapi

    index = BM25Okapi([simple_tokenize(doc.page_content) for doc in corpus]) if corpus else None

    if settings.use_remote_qdrant:
        _mem_corpus = list(corpus)
        _mem_index = index
        return

    if index is None:
        _INDEX_FILE.unlink(missing_ok=True)
        _CORPUS_FILE.unlink(missing_ok=True)
        return
    _save_corpus(corpus)
    _save_index(index)


def rebuild_from_vectorstore() -> int:
    """Rebuild the BM25 index from every chunk stored in Qdrant. Returns corpus size."""
    from app.services.vectorstore import scroll_all_documents

    with _lock:
        corpus = scroll_all_documents()
        build_index(corpus)
    logger.info("BM25 rebuilt from Qdrant: %d chunks", len(corpus))
    return len(corpus)


def add_chunks_to_index(new_chunks: List[Document]) -> None:
    with _lock:
        existing = _load_corpus()
        build_index(existing + new_chunks)


def remove_document_from_index(source: str) -> None:
    with _lock:
        corpus = _load_corpus()
        filtered = [d for d in corpus if d.metadata.get("source") != source]
        if len(filtered) < len(corpus):
            build_index(filtered)


def get_corpus_size() -> int:
    return len(_load_corpus())


def _matches_filter(doc: Document, filter_metadata: Optional[Dict[str, Any]]) -> bool:
    if not filter_metadata:
        return True
    meta = doc.metadata or {}
    for key, value in filter_metadata.items():
        if str(meta.get(key, "")).strip() != str(value).strip():
            return False
    return True


def search(
    query: str,
    top_k: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> List[Tuple[Document, float]]:
    index = _load_index()
    corpus = _load_corpus()

    if index is None or not corpus:
        return []

    tokens = simple_tokenize(query)
    if not tokens:
        return []

    scores = index.get_scores(tokens)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    filtered = [
        (corpus[i], float(s))
        for i, s in ranked
        if s > 0 and _matches_filter(corpus[i], filter_metadata)
    ]
    return filtered[:top_k]
