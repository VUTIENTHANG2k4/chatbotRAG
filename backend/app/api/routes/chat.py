from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import ask, ask_stream_async
from app.services.vectorstore import get_collection_stats

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


def _ensure_indexed():
    if get_collection_stats()["total_chunks"] == 0:
        raise HTTPException(
            status_code=409,
            detail="Chưa có tài liệu nào được nạp. Vui lòng upload tài liệu trước.",
        )


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Synchronous Q&A — returns full answer + sources in one response."""
    _ensure_indexed()

    try:
        result = ask(
            question=req.question,
            provider=req.provider,
            top_k=req.top_k,
            chat_history=[m.model_dump() for m in req.chat_history],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(**result)


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """Streaming Q&A using Server-Sent Events (SSE).

    Event types:
      - sources : JSON array of source citations (sent first)
      - token   : a chunk of the LLM-generated answer
      - done    : end of stream
      - error   : error message
    """
    _ensure_indexed()

    async def event_generator() -> AsyncIterator[bytes]:
        try:
            stream, sources = await ask_stream_async(
                question=req.question,
                provider=req.provider,
                top_k=req.top_k,
                chat_history=[m.model_dump() for m in req.chat_history],
            )

            yield _sse("sources", json.dumps(sources, ensure_ascii=False))

            async for token in stream:
                if token:
                    yield _sse("token", json.dumps(token, ensure_ascii=False))

            yield _sse("done", "{}")
        except Exception as e:
            logger.exception("Stream failed")
            yield _sse("error", json.dumps({"message": str(e)}, ensure_ascii=False))

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
