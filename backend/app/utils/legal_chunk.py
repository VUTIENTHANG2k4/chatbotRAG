"""Split Vietnamese legal text into Điều-level chunks.

Every emitted piece of an article starts with that article's heading, including
when the body is longer than ``chunk_size`` and is split by khoản.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Official "Điều" plus OCR variants seen in the scanned VBHN: "Điêu", "Dieu".
_ARTICLE_LABEL = r"(?:Điều|Điêu|ĐIỀU|DIEU|Dieu)"
# A heading has a period or colon after the article number ("Điều 20. ...").
# Citations ("Điều 18,", "Điều này") do not, so they stay inside the body.
_HEADING_TOKEN = re.compile(rf"({_ARTICLE_LABEL})\s*(\d+[a-zA-Z]?)\s*[.:]")
_CANDIDATE = re.compile(
    rf"(?m)^[ \t]*({_ARTICLE_LABEL}\s+(\d+[a-zA-Z]?))[ \t]*([.:])?[ \t]*(.*)$"
)
# "lao động1. Được" — khoản number glued to the previous word.
_GLUED_KHOAN = re.compile(r"(?<=[^\W\d_])(?=\d{1,2}\.\s)")
_KHOAN_SPLIT = re.compile(r"(?m)(?=^[ \t]*\d{1,2}[.)][ \t]+)")
# VBHN footnotes quote amending laws ("Luật Dân số số 113/2025/QH15 ... quy định
# như sau: “Điều 30. Hiệu lực thi hành ...”"). They sit at the page bottom and
# must not be read as articles of the consolidated code.
_AMENDING_NOTE = re.compile(
    r"(?:Luật|Bộ luật)[^\n]{0,80}?số\s*\d+/\d{4}/QH\d+.{0,200}?"
    r"(?:có căn cứ ban hành|quy định như sau)",
    re.S,
)
NOTE_HEADING = "Ghi chú văn bản hợp nhất (trích văn bản sửa đổi)"
# A real next article is numbered above the previous one; OCR may drop a few.
_MAX_ARTICLE_GAP = 10


@dataclass(frozen=True)
class LegalChunk:
    text: str
    page: int
    dieu: str
    dieu_heading: str


def chunk_legal_pages(
    pages: list[tuple[str, int]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[LegalChunk]:
    """Join pages, split on Điều, then pack each article into size-limited pieces."""
    normalized_pages = [
        (_normalize_article_breaks(text), page) for text, page in pages
    ]
    combined, spans = _join_pages(normalized_pages)
    if not combined.strip():
        return []

    combined, notes = _extract_notes(combined, spans)
    articles = _find_articles(combined)
    pieces: list[tuple[str, str, str, int]] = []
    for start, note in notes:
        for text in _pack_article(NOTE_HEADING, note, chunk_size, chunk_overlap):
            pieces.append((text, "", NOTE_HEADING, start))

    if not articles:
        for window in _char_windows(combined.strip(), chunk_size, chunk_overlap):
            pieces.append((window, "", "", 0))
    else:
        first_start = articles[0][0]
        preamble = combined[:first_start].strip()
        if preamble:
            for window in _char_windows(preamble, chunk_size, chunk_overlap):
                pieces.append((window, "", "", 0))
        for start, _end, heading, num, body in articles:
            for text in _pack_article(heading, body, chunk_size, chunk_overlap):
                pieces.append((text, num, heading, start))

    pieces.sort(key=lambda p: p[3])
    chunks: list[LegalChunk] = []
    for text, num, heading, start in pieces:
        if not text.strip():
            continue
        chunks.append(
            LegalChunk(
                text=text.strip(),
                page=_page_at(spans, start),
                dieu=num,
                dieu_heading=heading,
            )
        )
    return chunks


def _join_pages(pages: list[tuple[str, int]]) -> tuple[str, list[tuple[int, int, int]]]:
    parts: list[str] = []
    spans: list[tuple[int, int, int]] = []
    cursor = 0
    for text, page in pages:
        cleaned = (text or "").strip()
        if not cleaned:
            continue
        if parts:
            parts.append("\n\n")
            cursor += 2
        start = cursor
        parts.append(cleaned)
        cursor += len(cleaned)
        spans.append((start, cursor, page))
    return "".join(parts), spans


def _extract_notes(
    text: str, spans: list[tuple[int, int, int]]
) -> tuple[str, list[tuple[int, str]]]:
    """Cut amending-law footnotes out of the text, each up to the end of its page.

    The cut range is blanked with newlines of the same length so page offsets
    stay valid. Returns the cleaned text and (start, note_text) pairs.
    """
    notes: list[tuple[int, str]] = []
    out = text
    pos = 0
    while True:
        match = _AMENDING_NOTE.search(out, pos)
        if not match:
            break
        start = out.rfind("\n", 0, match.start()) + 1
        end = next((e for s, e, _ in spans if s <= start < e), len(out))
        note = out[start:end].strip()
        if note:
            notes.append((start, note))
        out = out[:start] + "\n" * (end - start) + out[end:]
        pos = end
    return out, notes


def _normalize_article_breaks(text: str) -> str:
    """Put each article heading on its own line, including OCR-glued headings."""

    def _break_heading(match: re.Match[str]) -> str:
        if match.start() == 0 or text[match.start() - 1] == "\n":
            return match.group(0)
        return "\n" + match.group(0)

    text = _HEADING_TOKEN.sub(_break_heading, text)
    return _GLUED_KHOAN.sub("\n", text)


def _classify_rest(rest: str) -> str:
    rest = rest.strip()
    if not rest:
        return "empty"
    ch = rest[0]
    if ch.isdigit():
        return "body"
    if ch.isalpha() and not ch.islower():
        return "title"
    return "citation"


def _next_line(text: str, pos: int) -> str:
    nxt = text[pos + 1 :] if pos < len(text) else ""
    for line in nxt.split("\n"):
        if line.strip():
            return line.strip()
    return ""


def _keep_candidate(match: re.Match[str], text: str) -> bool:
    rest = match.group(4) or ""
    kind = _classify_rest(rest)
    if kind == "citation":
        return False
    if kind == "empty" and not match.group(3):
        nxt = _next_line(text, match.end())
        if nxt and _classify_rest(nxt) == "citation":
            return False
    return True


def _split_title_and_inline_body(rest: str) -> tuple[str, str]:
    rest = rest.strip()
    if re.match(r"\d{1,2}[.)]\s", rest):
        return "", rest
    khoan = re.search(r"(?<=\s)(?=\d{1,2}[.)]\s)", rest)
    if khoan and khoan.start() <= 160:
        return rest[: khoan.start()].strip(" ."), rest[khoan.start() :].strip()
    dot = rest.find(". ")
    if 0 < dot <= 160:
        return rest[:dot].strip(), rest[dot + 2 :].strip()
    return rest.strip(" ."), ""


def _heading_and_inline_body(match: re.Match[str]) -> tuple[str, str]:
    num = match.group(2)
    rest = (match.group(4) or "").strip()
    kind = _classify_rest(rest)
    title = ""
    inline_body = ""
    if kind == "title":
        title, inline_body = _split_title_and_inline_body(rest)
    elif kind == "body":
        inline_body = rest
    heading = f"Điều {num}. {title}".rstrip() if title else f"Điều {num}."
    if heading.endswith(".."):
        heading = heading[:-1]
    return heading, inline_body


def _in_sequence(matches: list[re.Match[str]]) -> list[re.Match[str]]:
    """Keep headings whose number moves forward.

    A number at or below the previous article is a stray heading. A big jump is
    stray only when the next heading falls back below it (one-off outlier).
    """
    nums = [int(re.match(r"\d+", m.group(2)).group()) for m in matches]
    kept: list[re.Match[str]] = []
    last = 0
    for i, (match, num) in enumerate(zip(matches, nums)):
        if num <= last:
            continue
        nxt = nums[i + 1] if i + 1 < len(nums) else None
        if num - last > _MAX_ARTICLE_GAP and nxt is not None and last < nxt < num:
            continue
        kept.append(match)
        last = num
    return kept


def _find_articles(text: str) -> list[tuple[int, int, str, str, str]]:
    matches = _in_sequence(
        [m for m in _CANDIDATE.finditer(text) if _keep_candidate(m, text)]
    )
    articles: list[tuple[int, int, str, str, str]] = []
    for i, match in enumerate(matches):
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading, inline_body = _heading_and_inline_body(match)
        after = re.sub(r"\n{3,}", "\n\n", text[match.end() : next_start]).strip()
        body_parts = [part for part in (inline_body, after) if part]
        body = "\n".join(body_parts).strip()
        articles.append((match.start(), next_start, heading, match.group(2), body))
    return articles


def _pack_article(heading: str, body: str, chunk_size: int, overlap: int) -> list[str]:
    heading = heading.strip()
    body = body.strip()
    if not body:
        return [heading]
    full = f"{heading}\n{body}"
    if len(full) <= chunk_size:
        return [full]

    budget = max(chunk_size - len(heading) - 1, 120)
    segments = [seg.strip("\n") for seg in _KHOAN_SPLIT.split(body) if seg.strip()]
    if not segments:
        segments = [body]

    packed: list[str] = []
    buf: list[str] = []
    buf_len = 0

    def flush() -> None:
        nonlocal buf, buf_len
        if buf:
            packed.append(heading + "\n" + "\n".join(buf).strip())
            buf = []
            buf_len = 0

    for seg in segments:
        if len(seg) > budget:
            flush()
            for window in _char_windows(seg, budget, overlap):
                packed.append(f"{heading}\n{window.strip()}")
            continue
        extra = len(seg) + (1 if buf else 0)
        if buf and buf_len + extra > budget:
            flush()
        buf.append(seg.strip())
        buf_len += len(seg) + (1 if buf_len else 0)
    flush()
    return packed or [full]


def _char_windows(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    overlap = max(0, min(overlap, size // 4))
    windows: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind(" ", start + size // 2, end)
            if cut != -1:
                end = cut
        piece = text[start:end].strip()
        if piece:
            windows.append(piece)
        if end >= len(text):
            break
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start
    return windows


def _page_at(spans: list[tuple[int, int, int]], offset: int) -> int:
    if not spans:
        return 1
    for start, end, page in spans:
        if start <= offset < end:
            return page
    return spans[-1][2]
