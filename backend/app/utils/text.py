from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Optional


_DOC_TYPE_PATTERNS = {
    "Bộ luật": r"bo[_\s-]?luat",
    "Luật": r"\bluat\b",
    "Văn bản hợp nhất": r"\bvbhn\b",
    "Nghị định": r"nghi[_\s-]?dinh|\bnd\b",
    "Thông tư liên tịch": r"\bttlt\b",
    "Thông tư": r"thong[_\s-]?tu|\btt\b",
    "Quyết định": r"quyet[_\s-]?dinh|\bqd\b",
    "Nghị quyết": r"nghi[_\s-]?quyet|\bnq\b",
    "Pháp lệnh": r"phap[_\s-]?lenh|\bpl\b",
    "Hiến pháp": r"hien[_\s-]?phap",
    "Chỉ thị": r"chi[_\s-]?thi|\bct\b",
    "Công văn": r"cong[_\s-]?van|\bcv\b",
}

_YEAR_PATTERN = re.compile(r"(19|20)\d{2}")
_NUMBER_PATTERN = re.compile(r"(\d+)[/_-](\d{4})")


def extract_metadata_from_filename(filename: str) -> dict:
    """Parse legal document metadata from a filename."""
    stem = Path(filename).stem
    name_normalized = _strip_accents(stem).lower()

    doc_type = _detect_doc_type(name_normalized)
    year = _detect_year(stem)
    number = _detect_number(stem)
    title = re.sub(r"[-_]+", " ", stem).strip()

    return {
        "source": filename,
        "title": title,
        "doc_type": doc_type,
        "year": year,
        "number": number,
    }


def _detect_doc_type(name_lower: str) -> str:
    for label, pattern in _DOC_TYPE_PATTERNS.items():
        if re.search(pattern, name_lower):
            return label
    return "Văn bản pháp luật"


def _detect_year(text: str) -> Optional[str]:
    match = _YEAR_PATTERN.search(text)
    return match.group(0) if match else None


def _detect_number(text: str) -> Optional[str]:
    match = _NUMBER_PATTERN.search(text)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    num_match = re.search(r"\b(\d{1,4})\b", text)
    return num_match.group(1) if num_match else None


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def simple_tokenize(text: str) -> list[str]:
    """Lowercase, remove punctuation, split by whitespace. Vietnamese-friendly."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return [t for t in text.split() if len(t) > 1]


def truncate_text(text: str, max_chars: int = 300) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def format_source_label(metadata: dict) -> str:
    parts = []
    if metadata.get("title"):
        parts.append(metadata["title"])
    if metadata.get("doc_type") and metadata.get("year"):
        parts.append(f"({metadata['doc_type']} {metadata['year']})")
    if metadata.get("page"):
        parts.append(f"— Trang {metadata['page']}")
    return " ".join(parts) if parts else metadata.get("source", "Không rõ nguồn")
