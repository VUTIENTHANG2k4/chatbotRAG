from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.document import (
    DeleteResponse,
    DocumentInfo,
    DocumentListResponse,
    IngestResponse,
    IngestResult,
)
from app.services.bm25_store import remove_document_from_index
from app.services.ingestion import ingest_bytes, ingest_all, SUPPORTED_EXTS
from app.services.vectorstore import (
    delete_document_by_source,
    get_collection_stats,
    list_indexed_documents,
)

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)

_ALLOWED_EXTS = SUPPORTED_EXTS  # pdf, docx, txt + png, jpg, jpeg, tiff, bmp, webp


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    docs = list_indexed_documents()
    stats = get_collection_stats()
    return DocumentListResponse(
        total_documents=len(docs),
        total_chunks=stats["total_chunks"],
        documents=[DocumentInfo(**d) for d in docs],
    )


@router.post("/upload", response_model=IngestResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    overwrite: bool = Query(default=False),
) -> IngestResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    results: List[IngestResult] = []

    for f in files:
        filename = f.filename or "unknown"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in _ALLOWED_EXTS:
            results.append(IngestResult(
                status="error",
                source=filename,
                reason=f"Unsupported file type '{ext}'. Allowed: pdf, docx, txt",
            ))
            continue

        data = await f.read()
        if len(data) > max_bytes:
            results.append(IngestResult(
                status="error",
                source=filename,
                reason=f"File too large (>{settings.max_upload_size_mb} MB)",
            ))
            continue

        try:
            result = ingest_bytes(filename, data, overwrite=overwrite)
            results.append(IngestResult(**result))
        except Exception as e:
            logger.exception("Ingestion failed for %s", filename)
            results.append(IngestResult(status="error", source=filename, reason=str(e)))

    return IngestResponse(results=results)


@router.post("/ingest-disk", response_model=IngestResponse)
async def ingest_disk(
    overwrite: bool = Query(default=False),
) -> IngestResponse:
    """Quét toàn bộ thư mục data/ (đệ quy) và nạp tất cả file chưa được index.
    Hỗ trợ: PDF (kể cả scan/ảnh), DOCX, TXT, PNG, JPG, TIFF, BMP, WEBP.
    """
    import asyncio

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, lambda: ingest_all(overwrite=overwrite))
    return IngestResponse(results=[IngestResult(**r) for r in results])


@router.delete("/{source}", response_model=DeleteResponse)
async def delete_document(source: str) -> DeleteResponse:
    ok_vector = delete_document_by_source(source)
    remove_document_from_index(source)

    # Remove physical file from data/ if it exists
    physical = settings.data_dir / source
    if physical.exists():
        try:
            physical.unlink()
            logger.info("Deleted physical file: %s", physical)
        except Exception as e:
            logger.warning("Could not delete physical file %s: %s", physical, e)

    return DeleteResponse(source=source, deleted=ok_vector)
