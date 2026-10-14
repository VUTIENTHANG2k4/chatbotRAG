from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=8000)


class Source(BaseModel):
    label: str
    source: str
    title: str = ""
    doc_type: str = ""
    year: Optional[str] = None
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    snippet: str
    rrf_score: float


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    chat_history: List[ChatMessage] = Field(default_factory=list, max_length=20)
    top_k: int = Field(default=5, ge=1, le=20)
    filter_doc_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Lọc theo loại văn bản, ví dụ: Bộ luật, Nghị định, Thông tư",
    )
    filter_year: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Lọc theo năm văn bản, ví dụ: 2019, 2020",
    )


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    query: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    llm_provider: str
    embed_provider: str
    total_chunks: int
