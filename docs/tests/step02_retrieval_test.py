"""
Bước 2 — Kiểm tra chất lượng retrieval
Chạy: python docs/tests/step02_retrieval_test.py
Không cần Ollama — chỉ test hybrid_search.
"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Thêm backend vào path
import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from app.services.hybrid_search import hybrid_search

# ── 10 câu hỏi kiểm tra đại diện ──────────────────────────────────────────
TEST_CASES = [
    {
        "id": 1,
        "query": "thời gian thử việc tối đa đối với lao động",
        "expect_keywords": ["thử việc", "ngày", "tháng"],
        "expect_dieu": "Điều 25",
    },
    {
        "id": 2,
        "query": "hợp đồng lao động không xác định thời hạn",
        "expect_keywords": ["không xác định thời hạn", "hợp đồng"],
        "expect_dieu": "Điều 20",
    },
    {
        "id": 3,
        "query": "điều khoản bắt buộc phải có trong hợp đồng lao động",
        "expect_keywords": ["lương", "công việc", "địa điểm"],
        "expect_dieu": "Điều 21",
    },
    {
        "id": 4,
        "query": "người lao động đơn phương chấm dứt hợp đồng",
        "expect_keywords": ["đơn phương", "chấm dứt", "báo trước"],
        "expect_dieu": "Điều 35",
    },
    {
        "id": 5,
        "query": "người sử dụng lao động đơn phương chấm dứt hợp đồng",
        "expect_keywords": ["người sử dụng lao động", "chấm dứt"],
        "expect_dieu": "Điều 36",
    },
    {
        "id": 6,
        "query": "sa thải trái pháp luật bồi thường người lao động",
        "expect_keywords": ["bồi thường", "chấm dứt trái"],
        "expect_dieu": "Điều 41",
    },
    {
        "id": 7,
        "query": "trợ cấp thôi việc thâm niên làm việc",
        "expect_keywords": ["thôi việc", "trợ cấp"],
        "expect_dieu": "Điều 46",
    },
    {
        "id": 8,
        "query": "thời giờ làm việc bình thường mỗi ngày mỗi tuần",
        "expect_keywords": ["giờ", "ngày", "tuần"],
        "expect_dieu": "Điều 105",
    },
    {
        "id": 9,
        "query": "nghỉ hằng năm ngày phép người lao động",
        "expect_keywords": ["nghỉ", "năm", "ngày"],
        "expect_dieu": "Điều 113",
    },
    {
        "id": 10,
        "query": "tiền lương tối thiểu vùng",
        "expect_keywords": ["lương tối thiểu", "vùng"],
        "expect_dieu": "Điều 91",
    },
]

# ── Hàm đánh giá ───────────────────────────────────────────────────────────

def keyword_hit(text: str, keywords: list[str]) -> list[str]:
    """Trả về keyword tìm thấy trong text (không phân biệt hoa thường)."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]

def run_tests(top_k: int = 5) -> list[dict]:
    results = []
    for tc in TEST_CASES:
        t0 = time.time()
        hits = hybrid_search(tc["query"], top_k=top_k)
        elapsed = round(time.time() - t0, 2)

        # Gộp toàn bộ text từ top-K chunk để tìm keyword
        combined_text = " ".join(doc.page_content for doc, _ in hits)
        found_kw = keyword_hit(combined_text, tc["expect_keywords"])
        kw_score = len(found_kw) / len(tc["expect_keywords"]) if tc["expect_keywords"] else 1

        # Snippet chunk đầu
        first_snippet = hits[0][0].page_content[:200].replace("\n", " ") if hits else "(không có kết quả)"
        first_rrf = round(hits[0][1], 4) if hits else 0

        passed = len(hits) > 0 and kw_score >= 0.5   # ít nhất 50% keyword tìm thấy

        results.append({
            "id": tc["id"],
            "query": tc["query"],
            "expect_dieu": tc["expect_dieu"],
            "num_hits": len(hits),
            "kw_found": found_kw,
            "kw_score": f"{kw_score:.0%}",
            "first_rrf": first_rrf,
            "first_snippet": first_snippet,
            "elapsed_s": elapsed,
            "pass": passed,
        })
    return results

# ── Chạy và in kết quả ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("BƯỚC 2 — KIỂM TRA RETRIEVAL (hybrid search, top_k=5)")
    print("=" * 70)

    results = run_tests(top_k=5)

    passed = [r for r in results if r["pass"]]
    failed = [r for r in results if not r["pass"]]

    for r in results:
        status = "✅ PASS" if r["pass"] else "❌ FAIL"
        print(f"\n[{r['id']:02d}] {status} — {r['query'][:55]}")
        print(f"     Kỳ vọng: {r['expect_dieu']} | Hits: {r['num_hits']} | RRF: {r['first_rrf']} | {r['elapsed_s']}s")
        print(f"     Keywords({r['kw_score']}): {r['kw_found']}")
        print(f"     Snippet: {r['first_snippet'][:120]}…")

    print("\n" + "=" * 70)
    print(f"KẾT QUẢ: {len(passed)}/10 PASS  |  {len(failed)}/10 FAIL")
    print("=" * 70)

    # Xuất JSON để lưu vào history
    out_path = os.path.join(os.path.dirname(__file__), "step02_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nKết quả chi tiết lưu tại: {out_path}")
