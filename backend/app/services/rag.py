from __future__ import annotations

import re
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from fastapi.concurrency import run_in_threadpool
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.services.hybrid_search import hybrid_search
from app.services.llm import get_llm
from app.utils.text import format_source_label, truncate_text


REFUSAL_ANSWER = (
    "Tôi không tìm thấy quy định liên quan trong tài liệu hiện có. "
    "Bạn nên tham khảo thêm từ cơ quan có thẩm quyền hoặc luật sư."
)
# The model words refusals freely ("không tìm thấy quy định cụ thể về X") and
# may tack on citations; "Tuy nhiên ..." marks a partial answer worth sources.
_REFUSAL_OPENING = "tôi không tìm thấy quy định"
_REFUSAL_ADVICE = "tham khảo thêm từ cơ quan có thẩm quyền"
_PARTIAL_ANSWER = re.compile(r"\btuy nhiên\b")

_SYSTEM_PROMPT = """Bạn là trợ lý pháp luật chuyên sâu về **hợp đồng lao động Việt Nam**, hỗ trợ cả người lao động (NLĐ) và người sử dụng lao động (NSDLĐ) tra cứu, hiểu và đối chiếu quy định pháp luật.

## Quy tắc bắt buộc (KHÔNG được vi phạm)
1. **Chỉ trả lời dựa trên [TÀI LIỆU THAM KHẢO]** bên dưới — không bịa đặt, không suy luận ngoài tài liệu.
2. Nếu thông tin không có trong tài liệu → trả lời: "__REFUSAL__"
3. **Luôn trích dẫn nguồn** theo dạng [1], [2]... tương ứng với tài liệu trong phần tham khảo.
4. Trả lời bằng **tiếng Việt**, rõ ràng, chính xác, dùng đúng thuật ngữ pháp lý.
5. **Giữ nguyên số liệu** có trong tài liệu: số ngày, giờ, tháng, năm, lần, phần trăm, mức tiền. Nếu có nhiều mức theo điều kiện, nêu đủ từng mức kèm điều kiện. Không thay số bằng lời chung chung. Không bịa số khi tài liệu không ghi số.

## Định dạng trả lời bắt buộc
Mỗi câu trả lời PHẢI có đủ 3 phần (dùng đúng tiêu đề):

**Quy định áp dụng:** Điều/khoản cụ thể và các con số có trong tài liệu, ví dụ "Điều 35, khoản 1 Bộ luật Lao động..."

**Căn cứ pháp lý:** Diễn giải hoặc trích dẫn từ tài liệu, kèm [số nguồn] như [1], [2]. Khi đoạn trích có con số, ghi đúng con số đó.

**Lưu ý thực tiễn:** Điều kiện, ngoại lệ hoặc quy trình liên quan (nếu có trong tài liệu), kể cả số liệu của từng trường hợp.

---
[TÀI LIỆU THAM KHẢO]
{context}
"""

_SYSTEM_PROMPT = _SYSTEM_PROMPT.replace("__REFUSAL__", REFUSAL_ANSWER)

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


def is_refusal(answer: str) -> bool:
    """A full refusal, where showing sources would only mislead."""
    text = (answer or "").strip().lower()
    return (
        text.startswith(_REFUSAL_OPENING)
        and _REFUSAL_ADVICE in text
        and not _PARTIAL_ANSWER.search(text)
    )


def _inputs(question: str, context: str, chat_history: Optional[List[Dict[str, str]]]) -> Dict[str, Any]:
    return {"context": context, "question": question, "chat_history": _to_messages(chat_history)}


def ask(
    question: str,
    top_k: int | None = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Synchronous RAG: retrieve → generate → return full answer + sources.

    No relevant chunk → refuse without calling the LLM.
    """
    top_k = top_k or settings.top_k
    docs_with_scores = hybrid_search(question, top_k=top_k, filter_metadata=filter_metadata)
    if not docs_with_scores:
        return {"answer": REFUSAL_ANSWER, "sources": [], "query": question}

    chain = _PROMPT | get_llm() | StrOutputParser()
    answer = chain.invoke(_inputs(question, _build_context(docs_with_scores), chat_history))
    sources = [] if is_refusal(answer) else _docs_to_sources(docs_with_scores)
    return {"answer": answer, "sources": sources, "query": question}


async def _single(text: str) -> AsyncIterator[str]:
    yield text


async def ask_stream_async(
    question: str,
    top_k: int | None = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[AsyncIterator[str], List[Dict[str, Any]]]:
    """Async streaming variant for FastAPI SSE endpoints.

    The caller sends sources after the answer and drops them on a refusal
    (see ``is_refusal``).
    """
    top_k = top_k or settings.top_k
    docs_with_scores = await run_in_threadpool(
        hybrid_search, question, top_k=top_k, filter_metadata=filter_metadata
    )
    if not docs_with_scores:
        return _single(REFUSAL_ANSWER), []

    chain = _PROMPT | get_llm() | StrOutputParser()
    stream = chain.astream(_inputs(question, _build_context(docs_with_scores), chat_history))
    return stream, _docs_to_sources(docs_with_scores)
