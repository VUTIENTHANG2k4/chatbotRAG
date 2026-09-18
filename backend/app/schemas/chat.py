from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


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
    question: str = Field(..., min_length=1)
    chat_history: List[ChatMessage] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    provider: Optional[str] = Field(default=None, description="ollama | openai | gemini")


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
