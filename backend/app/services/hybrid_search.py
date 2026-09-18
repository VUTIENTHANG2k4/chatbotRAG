from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document

from app.core.config import settings
from app.services.bm25_store import search as bm25_search
from app.services.embeddings import embed_query
from app.services.vectorstore import similarity_search


def _rrf_score(rank: int, k: int) -> float:
    return 1.0 / (k + rank)


def reciprocal_rank_fusion(
    ranked_lists: List[List[Document]],
    k: Optional[int] = None,
) -> List[Tuple[Document, float]]:
    """Fuse multiple ranked lists with RRF. Returns (Document, score) sorted desc."""
    k = k or settings.rrf_k
    score_map: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked, start=1):
            key = doc.page_content
            score_map[key] = score_map.get(key, 0.0) + _rrf_score(rank, k)
            doc_map[key] = doc

    fused = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
    return [(doc_map[key], score) for key, score in fused]


def hybrid_search(
    query: str,
    top_k: Optional[int] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> List[Tuple[Document, float]]:
    """Hybrid Search = Vector (Qdrant) + Keyword (BM25) + RRF fusion."""
    top_k = top_k or settings.top_k

    query_vec = embed_query(query)
    vector_hits = similarity_search(query_vec, top_k=top_k * 2, filter_metadata=filter_metadata)
    bm25_hits = bm25_search(query, top_k=top_k * 2, filter_metadata=filter_metadata)

    fused = reciprocal_rank_fusion(
        [[d for d, _ in vector_hits], [d for d, _ in bm25_hits]],
    )
    return fused[:top_k]
