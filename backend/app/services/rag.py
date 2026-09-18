from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.services.hybrid_search import hybrid_search
from app.services.llm import get_llm
from app.utils.text import format_source_label, truncate_text


_SYSTEM_PROMPT = """Bạn là trợ lý pháp luật chuyên sâu về **hợp đồng lao động Việt Nam**, hỗ trợ cả người lao động (NLĐ) và người sử dụng lao động (NSDLĐ) tra cứu, hiểu và đối chiếu quy định pháp luật.

## Quy tắc bắt buộc (KHÔNG được vi phạm)
1. **Chỉ trả lời dựa trên [TÀI LIỆU THAM KHẢO]** bên dưới — không bịa đặt, không suy luận ngoài tài liệu.
2. Nếu thông tin không có trong tài liệu → trả lời: "Tôi không tìm thấy quy định liên quan trong tài liệu hiện có. Bạn nên tham khảo thêm từ cơ quan có thẩm quyền hoặc luật sư."
3. **Luôn trích dẫn nguồn** theo dạng [1], [2]... tương ứng với tài liệu trong phần tham khảo.
4. Trả lời bằng **tiếng Việt**, rõ ràng, chính xác, dùng đúng thuật ngữ pháp lý.

## Định dạng trả lời bắt buộc
Mỗi câu trả lời PHẢI có đủ 3 phần (dùng đúng tiêu đề):

**Quy định áp dụng:** Điều/khoản cụ thể, ví dụ "Điều 35, khoản 2 Bộ luật Lao động 2019..."

**Căn cứ pháp lý:** Diễn giải hoặc trích dẫn từ tài liệu, kèm [số nguồn] như [1], [2].

**Lưu ý thực tiễn:** Điều kiện, ngoại lệ hoặc quy trình liên quan (nếu có trong tài liệu).

---
[TÀI LIỆU THAM KHẢO]
{context}
"""

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{question}"),
])


def _build_context(docs_with_scores: List[Tuple[Document, float]]) -> str:
    parts = []
    for i, (doc, _) in enumerate(docs_with_scores, start=1):
        label = format_source_label(doc.metadata)
        parts.append(f"[{i}] {label}\n{doc.page_content}\n")
    return "\n---\n".join(parts) if parts else "(Không có tài liệu liên quan)"


def _docs_to_sources(docs_with_scores: List[Tuple[Document, float]]) -> List[Dict[str, Any]]:
    sources = []
    seen = set()
    for doc, score in docs_with_scores:
        meta = doc.metadata
        key = (meta.get("source", ""), meta.get("page"), doc.page_content[:80])
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "label": format_source_label(meta),
            "source": meta.get("source", ""),
            "title": meta.get("title", ""),
            "doc_type": meta.get("doc_type", ""),
            "year": meta.get("year"),
            "page": meta.get("page"),
            "chunk_index": meta.get("chunk_index"),
            "snippet": truncate_text(doc.page_content, 300),
            "rrf_score": round(score, 4),
        })
    return sources


def _to_messages(history: Optional[List[Dict[str, str]]]):
    if not history:
        return []
    msgs = []
    for m in history:
        if m["role"] == "user":
            msgs.append(HumanMessage(content=m["content"]))
        else:
            msgs.append(AIMessage(content=m["content"]))
    return msgs


def ask(
    question: str,
    provider: str | None = None,
    top_k: int | None = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Synchronous RAG: retrieve → generate → return full answer + sources."""
    top_k = top_k or settings.top_k
    docs_with_scores = hybrid_search(question, top_k=top_k, filter_metadata=filter_metadata)
    context = _build_context(docs_with_scores)

    chain = _PROMPT | get_llm(provider) | StrOutputParser()
    answer = chain.invoke({
        "context": context,
        "question": question,
        "chat_history": _to_messages(chat_history),
    })

    return {
        "answer": answer,
        "sources": _docs_to_sources(docs_with_scores),
        "query": question,
    }


def ask_stream_sync(
    question: str,
    provider: str | None = None,
    top_k: int | None = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[Iterator[str], List[Dict[str, Any]]]:
    """Sync streaming variant: returns (token_iterator, sources)."""
    top_k = top_k or settings.top_k
    docs_with_scores = hybrid_search(question, top_k=top_k, filter_metadata=filter_metadata)
    context = _build_context(docs_with_scores)
    sources = _docs_to_sources(docs_with_scores)

    chain = _PROMPT | get_llm(provider) | StrOutputParser()
    stream = chain.stream({
        "context": context,
        "question": question,
        "chat_history": _to_messages(chat_history),
    })
    return stream, sources


async def ask_stream_async(
    question: str,
    provider: str | None = None,
    top_k: int | None = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[AsyncIterator[str], List[Dict[str, Any]]]:
    """Async streaming variant for FastAPI SSE endpoints."""
    top_k = top_k or settings.top_k
    docs_with_scores = hybrid_search(question, top_k=top_k, filter_metadata=filter_metadata)
    context = _build_context(docs_with_scores)
    sources = _docs_to_sources(docs_with_scores)

    chain = _PROMPT | get_llm(provider) | StrOutputParser()
    stream = chain.astream({
        "context": context,
        "question": question,
        "chat_history": _to_messages(chat_history),
    })
    return stream, sources
