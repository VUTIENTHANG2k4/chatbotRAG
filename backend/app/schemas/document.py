from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    source: str = Field(..., description="Filename of the document")
    title: str
    doc_type: str = ""
    year: Optional[str] = None
    chunk_count: int = 0


class DocumentListResponse(BaseModel):
    total_documents: int
    total_chunks: int
    documents: List[DocumentInfo]


class IngestResult(BaseModel):
    status: str  # "success" | "skipped" | "error"
    source: str
    pages: Optional[int] = None
    chunks: Optional[int] = None
    reason: Optional[str] = None


class IngestResponse(BaseModel):
    results: List[IngestResult]


class DeleteResponse(BaseModel):
    source: str
    deleted: bool
