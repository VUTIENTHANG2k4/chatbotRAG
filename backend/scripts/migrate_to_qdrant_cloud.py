"""Copy the local file-based Qdrant collection (vectors + payloads) to Qdrant Cloud.

Reuses the existing embeddings, so the scanned PDF is not OCR'd or re-embedded.

Run from backend/ (stop the local backend first: file-based Qdrant allows one client):
  QDRANT_URL=https://xxx.cloud.qdrant.io QDRANT_API_KEY=... python scripts/migrate_to_qdrant_cloud.py
  python scripts/migrate_to_qdrant_cloud.py --recreate   # drop the remote collection first
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qdrant_client import QdrantClient  # noqa: E402
from qdrant_client.models import PointStruct  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.services.vectorstore import ensure_collection  # noqa: E402

setup_logging()
logger = get_logger(__name__)

_BATCH = 128


def _read_local(client: QdrantClient, collection: str) -> list[PointStruct]:
    points: list[PointStruct] = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=collection,
            limit=_BATCH,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        points.extend(PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in batch)
        if offset is None:
            return points


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate local Qdrant collection to Qdrant Cloud")
    parser.add_argument("--recreate", action="store_true", help="Delete the remote collection before copying")
    args = parser.parse_args()

    url = os.getenv("QDRANT_URL", settings.qdrant_url).strip()
    api_key = os.getenv("QDRANT_API_KEY", settings.qdrant_api_key).strip()
    if not url:
        logger.error("QDRANT_URL is not set")
        return 1

    collection = settings.qdrant_collection
    local = QdrantClient(path=str(settings.qdrant_path))
    points = _read_local(local, collection)
    local.close()
    if not points:
        logger.error("Local collection '%s' at %s is empty", collection, settings.qdrant_path)
        return 1
    dim = len(points[0].vector)
    logger.info("Local: %d points, dim=%d", len(points), dim)

    remote = QdrantClient(url=url, api_key=api_key or None, timeout=60)
    existing = [c.name for c in remote.get_collections().collections]
    if args.recreate and collection in existing:
        logger.info("Deleting remote collection '%s'", collection)
        remote.delete_collection(collection)

    # ensure_collection creates payload indexes only when settings point at a remote Qdrant.
    settings.qdrant_url = url
    ensure_collection(remote, dim)

    for i in range(0, len(points), _BATCH):
        remote.upsert(collection_name=collection, points=points[i : i + _BATCH], wait=True)
        logger.info("Upserted %d/%d", min(i + _BATCH, len(points)), len(points))

    remote_count = remote.count(collection_name=collection, exact=True).count
    logger.info("Remote: %d points (local %d)", remote_count, len(points))
    if remote_count != len(points):
        logger.error("Point count mismatch")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
