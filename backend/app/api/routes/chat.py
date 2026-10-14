from __future__ import annotations

import json
from typing import AsyncIterator, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.core.ratelimit import rate_limit
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import ask, ask_stream_async, is_refusal
from app.services.vectorstore import get_collection_stats

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(rate_limit)])
logger = get_logger(__name__)


def _ensure_indexed():
    if get_collection_stats()["total_chunks"] == 0:
        raise HTTPException(
            status_code=409,
            detail="Chưa có tài liệu nào được nạp. Vui lòng upload tài liệu trước.",
        )


_BUSY_MARKERS = ("503", "unavailable", "high demand", "429", "quota", "rate limit")
# Hugging Face Inference answers 402 when the account runs out of credits.
_OUT_OF_CREDIT_MARKERS = ("402", "no remaining credits", "payment required")


def _upstream_error(e: Exception) -> tuple[int, str]:
    """Map a provider failure to a safe (status, message); details stay in the log."""
    text = str(e).lower()
    if any(m in text for m in _OUT_OF_CREDIT_MARKERS):
        return 503, "Dịch vụ AI tạm thời không khả dụng. Vui lòng thử lại sau."
    if any(m in text for m in _BUSY_MARKERS):
        return 503, "Dịch vụ AI đang quá tải. Vui lòng thử lại sau ít phút."
    return 500, "Không thể xử lý câu hỏi lúc này. Vui lòng thử lại sau."


def _build_filter_metadata(req: ChatRequest) -> Dict[str, str]:
    filter_metadata: Dict[str, str] = {}
    if req.filter_doc_type:
        filter_metadata["doc_type"] = req.filter_doc_type
    if req.filter_year:
        filter_metadata["year"] = req.filter_year
    return filter_metadata


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Synchronous Q&A — returns full answer + sources in one response."""
    _ensure_indexed()

    try:
        result = ask(
            question=req.question,
            top_k=req.top_k,
            chat_history=[m.model_dump() for m in req.chat_history],
            filter_metadata=_build_filter_metadata(req),
        )
    except Exception as e:
        logger.exception("Chat failed")
        status, message = _upstream_error(e)
        raise HTTPException(status_code=status, detail=message)

    return ChatResponse(**result)


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """Streaming Q&A using Server-Sent Events (SSE).

    Event types:
      - token   : a chunk of the LLM-generated answer
      - sources : JSON array of source citations, after the answer; empty when
                  the answer is the standard refusal
      - done    : end of stream
      - error   : error message
    """
    _ensure_indexed()

    async def event_generator() -> AsyncIterator[bytes]:
        try:
            stream, sources = await ask_stream_async(
                question=req.question,
                top_k=req.top_k,
                chat_history=[m.model_dump() for m in req.chat_history],
                filter_metadata=_build_filter_metadata(req),
            )

            answer = []
            async for token in stream:
                if token:
                    answer.append(token)
                    yield _sse("token", json.dumps(token, ensure_ascii=False))

            if is_refusal("".join(answer)):
                sources = []
            yield _sse("sources", json.dumps(sources, ensure_ascii=False))

            yield _sse("done", "{}")
        except Exception as e:
            logger.exception("Stream failed")
            _, message = _upstream_error(e)
            yield _sse("error", json.dumps({"message": message}, ensure_ascii=False))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _sse(event: str, data: str) -> bytes:
    """Format a single Server-Sent Event."""
    return f"event: {event}\ndata: {data}\n\n".encode("utf-8")
