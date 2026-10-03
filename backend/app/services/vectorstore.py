from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


_PAYLOAD_INDEX_FIELDS = ("source", "doc_type", "year", "dieu")
_SCROLL_BATCH = 256


@lru_cache(maxsize=1)
def _get_client():
    """Cached Qdrant client: remote when QDRANT_URL is set, else local file-based."""
    from qdrant_client import QdrantClient

    if settings.use_remote_qdrant:
        logger.info("Connecting to remote Qdrant at %s", settings.qdrant_url)
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=30,
            prefer_grpc=False,
        )
    return QdrantClient(path=str(settings.qdrant_path))


def ensure_collection(client: Any, vector_size: int) -> None:
    from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        logger.info("Creating Qdrant collection '%s' (dim=%d)",
                    settings.qdrant_collection, vector_size)
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    # Local mode ignores payload indexes; remote Qdrant needs them for filters.
    if settings.use_remote_qdrant:
        for field in _PAYLOAD_INDEX_FIELDS:
            try:
                client.create_payload_index(
                    collection_name=settings.qdrant_collection,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception as e:
                logger.debug("Payload index %s not created: %s", field, e)


def _ensure_collection(vector_size: int) -> None:
    ensure_collection(_get_client(), vector_size)


def upsert_chunks(chunks: List[Document], embeddings: List[List[float]]) -> List[str]:
    from qdrant_client.models import PointStruct

    if not chunks:
        return []

    _ensure_collection(len(embeddings[0]))
    client = _get_client()

    points, ids = [], []
    for doc, vector in zip(chunks, embeddings):
        pid = str(uuid.uuid4())
        ids.append(pid)
        payload = {**doc.metadata, "text": doc.page_content}
        points.append(PointStruct(id=pid, vector=vector, payload=payload))

    client.upsert(collection_name=settings.qdrant_collection, points=points)
    return ids


def similarity_search(
    query_vector: List[float],
    top_k: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> List[Tuple[Document, float]]:
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    qdrant_filter = None
    if filter_metadata:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filter_metadata.items()
        ]
        qdrant_filter = Filter(must=conditions)

    try:
        # qdrant-client >= 1.7 uses query_points(); .search() was removed in 1.14+
        response = _get_client().query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        hits = response.points
    except Exception as e:
        logger.warning("Vector search failed: %s", e)
        return []

    out = []
    for hit in hits:
        payload = dict(hit.payload)
        text = payload.pop("text", "")
        doc = Document(
            page_content=text,
            metadata={**payload, "point_id": hit.id},
        )
        out.append((doc, float(hit.score)))
    return out


def delete_document_by_source(source: str) -> bool:
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    try:
        _get_client().delete(
            collection_name=settings.qdrant_collection,
            points_selector=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=source))]
            ),
        )
        return True
    except Exception as e:
        logger.warning("Delete failed for %s: %s", source, e)
        return False


def _scroll_payloads() -> List[Dict[str, Any]]:
    """All point payloads in the collection, paginated."""
    client = _get_client()
    payloads: List[Dict[str, Any]] = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=_SCROLL_BATCH,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        payloads.extend(dict(p.payload or {}) for p in points)
        if offset is None:
            break
    return payloads


def scroll_all_documents() -> List[Document]:
    """Every stored chunk as a Document (text + metadata), for rebuilding BM25."""
    try:
        payloads = _scroll_payloads()
    except Exception as e:
        logger.warning("Scroll failed: %s", e)
        return []
    docs: List[Document] = []
    for payload in payloads:
        text = payload.pop("text", "")
        docs.append(Document(page_content=text, metadata=payload))
    docs.sort(key=lambda d: (str(d.metadata.get("source", "")), d.metadata.get("chunk_index") or 0))
    return docs


def list_indexed_documents() -> List[Dict[str, Any]]:
    try:
        all_points = _scroll_payloads()
    except Exception:
        return []

    doc_map: Dict[str, Dict[str, Any]] = {}
    for payload in all_points:
        source = payload.get("source", "unknown")
        if source not in doc_map:
            doc_map[source] = {
                "source": source,
                "title": payload.get("title", source),
                "doc_type": payload.get("doc_type", ""),
                "year": payload.get("year"),
                "chunk_count": 0,
            }
        doc_map[source]["chunk_count"] += 1

    return sorted(doc_map.values(), key=lambda d: d["source"])


def document_exists(source: str) -> bool:
    return any(d["source"] == source for d in list_indexed_documents())


def get_collection_stats() -> Dict[str, Any]:
    try:
        info = _get_client().get_collection(settings.qdrant_collection)
        return {
            "total_chunks": info.points_count or 0,
            "vector_size": info.config.params.vectors.size,
            "status": str(info.status),
        }
    except Exception:
        return {"total_chunks": 0, "vector_size": 0, "status": "not_created"}
