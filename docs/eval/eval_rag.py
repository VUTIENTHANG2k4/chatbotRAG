"""
Chấm golden set RAG — retrieval + generation.

Chạy từ thư mục gốc repo:
  python docs/eval/eval_rag.py --validate
  python docs/eval/eval_rag.py --mode retrieval
  python docs/eval/eval_rag.py --mode generation --limit 3
  python docs/eval/eval_rag.py --mode both --ids E01,H22,O01

Không cần Ollama cho --mode retrieval / --validate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = Path(__file__).with_name("golden_set.json")
RESULTS_DIR = Path(__file__).with_name("results")

# ── Chuẩn hoá tiếng Việt (khớp OCR mất dấu) ────────────────────────────────


def strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")


def normalize(text: str) -> str:
    text = strip_accents(text or "").lower()
    text = text.replace("%", " % ")
    text = re.sub(r"\b0+(\d+)\b", r"\1", text)
    text = re.sub(r"[^a-z0-9%\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_dieu_nums(text: str) -> set[int]:
    """Lấy số Điều được nhắc trong text (OCR: Điều / Diêu / Dieu)."""
    t = strip_accents(text or "").lower()
    nums = {int(n) for n in re.findall(r"\bdi[eé]u\s+(\d+)\b", t)}
    nums |= {int(n) for n in re.findall(r"\bdieu\s+(\d+)\b", t)}
    return nums


def parse_dieu_label(label: str) -> int | None:
    m = re.search(r"(\d+)", label or "")
    return int(m.group(1)) if m else None


def contains_fact(haystack: str, needle: str) -> bool:
    return normalize(needle) in normalize(haystack) if needle.strip() else True


def coverage(haystack: str, facts: Iterable[str]) -> tuple[float, list[str], list[str]]:
    facts = [f for f in facts if f and str(f).strip()]
    if not facts:
        return 1.0, [], []
    found, missing = [], []
    for fact in facts:
        (found if contains_fact(haystack, fact) else missing).append(fact)
    return len(found) / len(facts), found, missing


# ── Citation / refusal ─────────────────────────────────────────────────────

_CITE_RE = re.compile(r"\[(\d+)\]")

REFUSAL_HINTS = [
    "khong tim thay",
    "khong co trong tai lieu",
    "tai lieu hien co",
    "ngoai pham vi",
    "khong nam trong tai lieu",
    "khong co quy dinh",
    "nen tham khao",
    "co quan co tham quyen",
    "luat su",
]


def citation_numbers(answer: str) -> list[int]:
    return [int(n) for n in _CITE_RE.findall(answer or "")]


def is_refusal(answer: str) -> bool:
    n = normalize(answer)
    return any(h in n for h in REFUSAL_HINTS)


# ── Load dataset ───────────────────────────────────────────────────────────

def load_golden(path: Path = GOLDEN_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"] if isinstance(data, dict) else data
    return {
        "meta": data.get("meta", {}) if isinstance(data, dict) else {},
        "items": items,
    }


def validate_golden(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    items: list[dict[str, Any]] = data["items"]
    if len(items) != 100:
        errors.append(f"Kỳ vọng 100 câu, thực tế {len(items)}")

    counts = {"easy": 0, "medium": 0, "hard": 0, "ood": 0}
    ids: set[str] = set()
    required = ["id", "difficulty", "type", "question", "expect_dieu", "gold_answer"]
    for i, it in enumerate(items):
        loc = it.get("id", f"index={i}")
        for k in required:
            if k not in it:
                errors.append(f"{loc}: thiếu field '{k}'")
        did = it.get("id")
        if did in ids:
            errors.append(f"Trùng id: {did}")
        ids.add(did)
        diff = it.get("difficulty")
        if diff in counts:
            counts[diff] += 1
        else:
            errors.append(f"{loc}: difficulty không hợp lệ: {diff}")
        if it.get("type") == "in_scope" and not it.get("expect_dieu"):
            errors.append(f"{loc}: in_scope phải có expect_dieu")
        if it.get("type") == "out_of_scope" and not it.get("expect_refusal", False):
            errors.append(f"{loc}: out_of_scope phải expect_refusal=true")
        if not str(it.get("question", "")).strip():
            errors.append(f"{loc}: question rỗng")

    expected_counts = {"easy": 25, "medium": 30, "hard": 25, "ood": 20}
    for k, v in expected_counts.items():
        if counts[k] != v:
            errors.append(f"Số câu {k}: kỳ vọng {v}, thực tế {counts[k]}")
    return errors


# ── Retrieval scoring ──────────────────────────────────────────────────────

def score_retrieval(item: dict[str, Any], chunks: list[str], k: int) -> dict[str, Any]:
    expected = {n for n in (parse_dieu_label(x) for x in item.get("expect_dieu") or []) if n}
    per_chunk_nums = [extract_dieu_nums(t) for t in chunks[:k]]
    found: set[int] = set()
    first_rank: int | None = None
    for rank, nums in enumerate(per_chunk_nums, start=1):
        hit = nums & expected
        if hit:
            found |= hit
            if first_rank is None:
                first_rank = rank

    recall = (len(found) / len(expected)) if expected else None
    mrr = (1.0 / first_rank) if first_rank else (None if expected else None)
    hit_any = bool(found) if expected else None
    hit_all = (found == expected) if expected else None

    if item.get("type") == "out_of_scope":
        passed = True
        skip_reason = "ood_retrieval_not_scored"
    else:
        # PASS: tìm được ít nhất 1 Điều kỳ vọng trong top-k
        passed = bool(hit_any)
        skip_reason = None

    return {
        "expected_dieu": sorted(expected),
        "found_dieu": sorted(found),
        "recall_at_k": None if recall is None else round(recall, 4),
        "hit_any": hit_any,
        "hit_all": hit_all,
        "mrr": None if mrr is None else round(mrr, 4),
        "first_rank": first_rank,
        "pass": passed,
        "skip_reason": skip_reason,
    }


# ── Generation scoring ─────────────────────────────────────────────────────

def score_generation(
    item: dict[str, Any],
    answer: str,
    sources: list[dict[str, Any]],
    retrieved_text: str,
) -> dict[str, Any]:
    must = item.get("must_contain") or []
    must_any_groups = item.get("must_contain_any") or []
    must_not = item.get("must_not_contain") or []

    cov, found, missing = coverage(answer, must)
    any_ok = True
    any_detail = []
    for group in must_any_groups:
        g_found = [f for f in group if contains_fact(answer, f)]
        ok = len(g_found) > 0 if group else True
        any_ok = any_ok and ok
        any_detail.append({"group": group, "found": g_found, "ok": ok})

    forbidden_hit = [f for f in must_not if contains_fact(answer, f)]
    cites = citation_numbers(answer)
    n_src = len(sources or [])
    grounded = all(1 <= n <= n_src for n in cites) if cites else False
    present = bool(cites) or "tai lieu tham khao" in normalize(answer)

    answer_dieu = extract_dieu_nums(answer)
    ctx_dieu = extract_dieu_nums(retrieved_text)
    expected = {n for n in (parse_dieu_label(x) for x in item.get("expect_dieu") or []) if n}
    hallucinated_dieu = sorted(n for n in answer_dieu if n not in ctx_dieu and n not in expected)
    refusal = is_refusal(answer)

    if item.get("expect_refusal"):
        passed = refusal
        fail_reasons = [] if passed else ["no_refusal"]
    else:
        fail_reasons = []
        if cov < 0.5:
            fail_reasons.append("key_fact_coverage<0.5")
        if not any_ok:
            fail_reasons.append("must_contain_any_miss")
        if forbidden_hit:
            fail_reasons.append("must_not_contain")
        if not present:
            fail_reasons.append("no_citation")
        passed = not fail_reasons

    return {
        "key_fact_coverage": round(cov, 4),
        "facts_found": found,
        "facts_missing": missing,
        "must_contain_any": any_detail,
        "forbidden_hit": forbidden_hit,
        "citation_present": present,
        "citation_ids": cites,
        "citation_grounded": grounded,
        "hallucinated_dieu": hallucinated_dieu,
        "refusal": refusal,
        "pass": passed,
        "fail_reasons": fail_reasons,
    }


# ── Runners ────────────────────────────────────────────────────────────────

def _backend_on_path() -> None:
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)


def run_retrieval(items: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    _backend_on_path()
    from app.services.hybrid_search import hybrid_search

    rows = []
    for it in items:
        t0 = time.time()
        hits = hybrid_search(it["question"], top_k=top_k)
        elapsed = round(time.time() - t0, 3)
        chunks = [doc.page_content for doc, _ in hits]
        scores = [round(float(s), 4) for _, s in hits]
        ret = score_retrieval(it, chunks, top_k)
        rows.append({
            "id": it["id"],
            "difficulty": it["difficulty"],
            "type": it["type"],
            "question": it["question"],
            "elapsed_s": elapsed,
            "num_hits": len(hits),
            "rrf_top": scores[0] if scores else 0,
            "snippets": [c[:180].replace("\n", " ") for c in chunks[:3]],
            "retrieval": ret,
        })
    return rows


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def run_generation(
    items: list[dict[str, Any]],
    top_k: int,
    retrieval_rows: list[dict[str, Any]] | None = None,
    checkpoint_path: Path | None = None,
    resume: bool = False,
) -> list[dict[str, Any]]:
    _backend_on_path()
    from app.services.rag import ask

    by_id = {r["id"]: r for r in (retrieval_rows or [])}
    rows: list[dict[str, Any]] = []
    done_ids: set[str] = set()
    if resume and checkpoint_path and checkpoint_path.exists():
        prev = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        rows = list(prev.get("generation") or [])
        done_ids = {r["id"] for r in rows}
        print(f"Resume: đã có {len(done_ids)} câu trong {checkpoint_path}", flush=True)

    total = len(items)
    for i, it in enumerate(items, start=1):
        if it["id"] in done_ids:
            print(f"[GEN {i}/{total}] {it['id']} skip (resume)", flush=True)
            continue
        t0 = time.time()
        try:
            result = ask(question=it["question"], top_k=top_k)
            err = None
        except Exception as e:  # noqa: BLE001 — CLI eval must continue
            result = {"answer": "", "sources": []}
            err = str(e)
        elapsed = round(time.time() - t0, 2)
        answer = result.get("answer") or ""
        sources = result.get("sources") or []
        retrieved_text = " ".join(
            (s.get("snippet") or "") + " " + (s.get("label") or "") for s in sources
        )
        gen = score_generation(it, answer, sources, retrieved_text)
        ret_row = by_id.get(it["id"])
        row = {
            "id": it["id"],
            "difficulty": it["difficulty"],
            "type": it["type"],
            "question": it["question"],
            "elapsed_s": elapsed,
            "error": err,
            "answer": answer,
            "answer_preview": answer[:500],
            "n_sources": len(sources),
            "generation": gen,
            "retrieval": None if ret_row is None else ret_row.get("retrieval"),
        }
        rows.append(row)
        mark = "PASS" if gen["pass"] else "FAIL"
        fr = ",".join(gen["fail_reasons"]) or "ok"
        print(
            f"[GEN {i}/{total}] {it['id']} {mark} {elapsed}s cov={gen['key_fact_coverage']} "
            f"cite={gen['citation_present']} {fr}",
            flush=True,
        )
        if checkpoint_path:
            _save_json(checkpoint_path, {
                "mode": "generation",
                "partial": True,
                "done": len(rows),
                "total": total,
                "generation": rows,
                "generation_summary": summarize(rows, "generation"),
            })
    return rows


def summarize(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    scored = [r for r in rows if r.get(key) and r[key].get("skip_reason") is None]
    passed = [r for r in scored if r[key].get("pass")]
    by_diff: dict[str, dict[str, int]] = {}
    for r in scored:
        d = r["difficulty"]
        by_diff.setdefault(d, {"pass": 0, "total": 0})
        by_diff[d]["total"] += 1
        if r[key].get("pass"):
            by_diff[d]["pass"] += 1

    extra: dict[str, Any] = {}
    if key == "retrieval":
        rec = [r["retrieval"]["recall_at_k"] for r in scored if r["retrieval"].get("recall_at_k") is not None]
        mrr = [r["retrieval"]["mrr"] for r in scored if r["retrieval"].get("mrr")]
        extra = {
            "macro_recall_at_k": round(sum(rec) / len(rec), 4) if rec else None,
            "mean_mrr": round(sum(mrr) / len(mrr), 4) if mrr else None,
        }
    if key == "generation":
        cov = [r["generation"]["key_fact_coverage"] for r in rows if r["type"] == "in_scope"]
        cite = [1 for r in rows if r["type"] == "in_scope" and r["generation"].get("citation_present")]
        grounded = [1 for r in rows if r["type"] == "in_scope" and r["generation"].get("citation_grounded")]
        hallu = [1 for r in rows if r["generation"].get("hallucinated_dieu")]
        refusal_rows = [r for r in rows if r["type"] == "out_of_scope"]
        extra = {
            "mean_key_fact_coverage": round(sum(cov) / len(cov), 4) if cov else None,
            "citation_rate": round(len(cite) / max(1, len([r for r in rows if r["type"] == "in_scope"])), 4),
            "citation_grounded_rate": round(len(grounded) / max(1, len([r for r in rows if r["type"] == "in_scope"])), 4),
            "hallucinated_dieu_rate": round(len(hallu) / max(1, len(rows)), 4),
            "refusal_accuracy": (
                round(sum(1 for r in refusal_rows if r["generation"].get("refusal")) / len(refusal_rows), 4)
                if refusal_rows else None
            ),
        }
    return {
        "n": len(scored),
        "pass": len(passed),
        "fail": len(scored) - len(passed),
        "pass_rate": round(len(passed) / len(scored), 4) if scored else None,
        "by_difficulty": by_diff,
        **extra,
    }


def print_summary(title: str, summary: dict[str, Any]) -> None:
    print(f"\n{'=' * 70}")
    print(title)
    print("=" * 70)
    print(f"PASS {summary['pass']}/{summary['n']}  ({(summary['pass_rate'] or 0):.0%})")
    for diff, st in summary.get("by_difficulty", {}).items():
        rate = st["pass"] / st["total"] if st["total"] else 0
        print(f"  {diff:8s} {st['pass']}/{st['total']} ({rate:.0%})")
    for k, v in summary.items():
        if k in {"n", "pass", "fail", "pass_rate", "by_difficulty"}:
            continue
        print(f"  {k}: {v}")


def filter_items(items: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    out = items
    if args.difficulty:
        allow = {x.strip() for x in args.difficulty.split(",")}
        out = [it for it in out if it["difficulty"] in allow]
    if args.ids:
        allow = {x.strip() for x in args.ids.split(",")}
        out = [it for it in out if it["id"] in allow]
    if args.offset:
        out = out[args.offset :]
    if args.limit is not None:
        out = out[: args.limit]
    return out


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(description="Chấm golden set ChatbotRAG")
    p.add_argument("--mode", choices=["validate", "retrieval", "generation", "both"], default="validate")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--ids", type=str, default="")
    p.add_argument("--difficulty", type=str, default="", help="easy,medium,hard,ood")
    p.add_argument("--golden", type=Path, default=GOLDEN_PATH)
    p.add_argument(
        "--checkpoint",
        type=Path,
        default=RESULTS_DIR / "generation_checkpoint.json",
        help="Lưu từng câu (generation) để resume nếu bị gián đoạn",
    )
    p.add_argument("--resume", action="store_true", help="Bỏ qua câu đã có trong checkpoint")
    args = p.parse_args()

    data = load_golden(args.golden)
    errors = validate_golden(data)
    print(f"Golden set: {args.golden}")
    print(f"Meta: {json.dumps(data['meta'], ensure_ascii=False)}")
    if errors:
        print("VALIDATE FAIL:")
        for e in errors:
            print(f"  - {e}")
        if args.mode == "validate":
            return 1
        print("Tiếp tục chấm dù schema có cảnh báo...")
    else:
        print("VALIDATE PASS — 100 câu (25 easy / 30 medium / 25 hard / 20 ood)")
        if args.mode == "validate":
            return 0

    items = filter_items(data["items"], args)
    print(f"Chấm {len(items)} câu | mode={args.mode} | top_k={args.top_k}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "mode": args.mode,
        "top_k": args.top_k,
        "n": len(items),
        "meta": data["meta"],
    }

    retrieval_rows: list[dict[str, Any]] = []
    if args.mode in {"retrieval", "both"}:
        retrieval_rows = run_retrieval(items, args.top_k)
        payload["retrieval_summary"] = summarize(retrieval_rows, "retrieval")
        payload["retrieval"] = retrieval_rows
        print_summary("RETRIEVAL", payload["retrieval_summary"])
        for r in retrieval_rows:
            mark = "✅" if r["retrieval"]["pass"] else "❌"
            info = r["retrieval"]
            print(
                f"  {mark} {r['id']}  found={info['found_dieu']} "
                f"expect={info['expected_dieu']}  R@{args.top_k}={info['recall_at_k']}  MRR={info['mrr']}"
            )

    if args.mode in {"generation", "both"}:
        gen_rows = run_generation(
            items,
            args.top_k,
            retrieval_rows,
            checkpoint_path=args.checkpoint,
            resume=args.resume,
        )
        payload["generation_summary"] = summarize(gen_rows, "generation")
        payload["generation"] = gen_rows
        payload["partial"] = False
        print_summary("GENERATION", payload["generation_summary"])
        for r in gen_rows:
            mark = "PASS" if r["generation"]["pass"] else "FAIL"
            fr = ",".join(r["generation"]["fail_reasons"]) or "ok"
            print(
                f"  {mark} {r['id']}  cov={r['generation']['key_fact_coverage']}  "
                f"cite={r['generation']['citation_present']}  {fr}",
                flush=True,
            )

    out_path = RESULTS_DIR / (
        "generation_full.json" if args.mode == "generation" else f"{args.mode}_{int(time.time())}.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
