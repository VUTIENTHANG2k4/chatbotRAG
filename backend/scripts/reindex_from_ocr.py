"""Rebuild one document's index from cached OCR page text.

The scanned VBHN has no text layer, so OCR runs once and the page text is kept
in ``storage/ocr/<file stem>.pages.json``. This script re-chunks from that cache
(no OCR), applies known page-order fixes of the scan, then replaces the
document's points in Qdrant and BM25.

Run from ``backend/``:
  python scripts/reindex_from_ocr.py --dry-run
  python scripts/reindex_from_ocr.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.documents import Document  # noqa: E402

from app.core.config import BASE_DIR  # noqa: E402
from app.services.ingestion import chunk_documents, index_documents  # noqa: E402
from app.utils.text import clean_text, extract_metadata_from_filename  # noqa: E402

OCR_DIR = BASE_DIR / "storage" / "ocr"

# Scan defects found by checking printed page numbers against article order.
# PDF pages 15 and 16 were scanned in swapped order (Điều 36 before Điều 34
# khoản 10–13 and Điều 35). Printed pages 33–34 (Điều 76–79) are absent from
# the PDF and cannot be recovered from this file.
PAGE_ORDER_FIXES: dict[str, list[tuple[int, int]]] = {
    "18-vbhn-vpqh.pdf": [(15, 16)],
}


def load_pages(source: str) -> list[Document]:
    cache = OCR_DIR / f"{Path(source).stem}.pages.json"
    data = json.loads(cache.read_text(encoding="utf-8"))
    pages = {p["page"]: p["text"] for p in data["pages"]}
    order = sorted(pages)
    for a, b in PAGE_ORDER_FIXES.get(source, []):
        ia, ib = order.index(a), order.index(b)
        order[ia], order[ib] = order[ib], order[ia]
    docs = []
    for page in order:
        text = clean_text(pages[page])
        if text.strip():
            docs.append(Document(page_content=text, metadata={"page": page}))
    return docs


def report(chunks: list[Document]) -> None:
    seq: list[int] = []
    for c in chunks:
        dieu = c.metadata.get("dieu")
        if dieu:
            n = int(re.match(r"\d+", dieu).group())
            if not seq or seq[-1] != n:
                seq.append(n)
    notes = sum(1 for c in chunks if not c.metadata.get("dieu") and c.metadata.get("dieu_heading"))
    print(f"chunks={len(chunks)} articles={len(seq)} unique={len(set(seq))} note_chunks={notes}")
    print("missing Điều 1-220:", sorted(set(range(1, 221)) - set(seq)))
    back = [(seq[i - 1], seq[i]) for i in range(1, len(seq)) if seq[i] <= seq[i - 1]]
    print("out of order:", back or "none")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="18-vbhn-vpqh.pdf")
    p.add_argument("--dry-run", action="store_true", help="Chỉ chunk và báo cáo, không ghi index")
    args = p.parse_args()

    docs = load_pages(args.source)
    chunks = chunk_documents(docs, extract_metadata_from_filename(args.source))
    report(chunks)
    if args.dry_run:
        return 0

    result = index_documents(args.source, docs, replace=True)
    print(result)
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
