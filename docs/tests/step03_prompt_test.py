"""
Bước 3 — Kiểm tra system prompt mới với Ollama
Chạy: python docs/tests/step03_prompt_test.py
Yêu cầu: Ollama đang chạy với qwen2.5:7b
"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from app.services.rag import ask

# 3 câu test đại diện — mỗi câu kiểm tra một khía cạnh prompt mới
TEST_CASES = [
    {
        "id": 1,
        "role": "NLĐ",
        "question": "Tôi muốn nghỉ việc, cần báo trước bao nhiêu ngày?",
        "check": [
            "báo trước",
            "ngày",
        ],
        "expect_sections": ["Quy định áp dụng", "Căn cứ pháp lý"],
    },
    {
        "id": 2,
        "role": "NSDLĐ",
        "question": "Doanh nghiệp có thể sa thải nhân viên vì lý do gì?",
        "check": [
            "kỷ luật",
            "sa thải",
        ],
        "expect_sections": ["Quy định áp dụng", "Căn cứ pháp lý"],
    },
    {
        "id": 3,
        "role": "cả hai",
        "question": "Thời gian thử việc tối đa là bao lâu?",
        "check": [
            "thử việc",
            "ngày",
        ],
        "expect_sections": ["Quy định áp dụng", "Căn cứ pháp lý"],
    },
]

DIVIDER = "=" * 70

_SEC_ALIASES = {
    "Quy định áp dụng": ["quy định áp dụng", "quy định", "điều ", "khoản "],
    "Căn cứ pháp lý":   ["căn cứ pháp lý", "căn cứ", "bộ luật", "luật lao động"],
}

def score_answer(answer: str, checks: list[str], sections: list[str]) -> dict:
    answer_lower = answer.lower()
    found_kw  = [kw for kw in checks if kw.lower() in answer_lower]
    found_sec = [s for s in sections
                 if any(alias in answer_lower for alias in _SEC_ALIASES.get(s, [s.lower()]))]
    has_citation = (any(f"[{i}]" in answer for i in range(1, 6))
                    or "tài liệu tham khảo" in answer_lower
                    or "điều " in answer_lower)
    return {
        "kw_hit":     f"{len(found_kw)}/{len(checks)} ({found_kw})",
        "section_hit":f"{len(found_sec)}/{len(sections)} ({found_sec})",
        "has_cite":   has_citation,
        "pass":       len(found_kw) == len(checks) and has_citation,
    }

def run():
    print(DIVIDER)
    print("BƯỚC 3 — TEST SYSTEM PROMPT MỚI (full RAG qua Ollama)")
    print(DIVIDER)

    passed = 0
    for tc in TEST_CASES:
        print(f"\n[{tc['id']}] Góc nhìn: {tc['role']}")
        print(f"    Câu hỏi: {tc['question']}")
        t0 = time.time()
        try:
            result = ask(question=tc["question"], top_k=5, provider="ollama")
        except Exception as e:
            print(f"    ❌ LỖI: {e}")
            continue
        elapsed = round(time.time() - t0, 1)

        answer  = result["answer"]
        sources = result["sources"]
        score   = score_answer(answer, tc["check"], tc["expect_sections"])

        status = "✅ PASS" if score["pass"] else "❌ FAIL"
        if score["pass"]:
            passed += 1

        print(f"    {status} | {elapsed}s | Sources: {len(sources)}")
        print(f"    Keywords : {score['kw_hit']}")
        print(f"    Sections : {score['section_hit']}")
        print(f"    Cite [N] : {'✅' if score['has_cite'] else '❌'}")
        print(f"\n    --- Câu trả lời ---")
        # In 600 ký tự đầu để xem cấu trúc
        preview = answer[:600].replace("\n", "\n    ")
        print(f"    {preview}")
        if len(answer) > 600:
            print(f"    ... [{len(answer)-600} ký tự còn lại]")
        print(f"\n    Nguồn trích dẫn:")
        for s in sources[:3]:
            print(f"      [{sources.index(s)+1}] {s['label']} (RRF={s['rrf_score']})")

    print(f"\n{DIVIDER}")
    print(f"KẾT QUẢ: {passed}/{len(TEST_CASES)} PASS")
    print(DIVIDER)

if __name__ == "__main__":
    run()
