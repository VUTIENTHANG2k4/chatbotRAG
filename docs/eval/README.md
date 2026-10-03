# Golden set RAG — Bộ luật Lao động (18/VBHN-VPQH)

Dataset: `golden_set.json` (100 câu, bám `backend/data/legal_documents/core/18-vbhn-vpqh.pdf`).

| Nhóm | Số câu | Ý nghĩa |
|------|--------|---------|
| easy | 25 | 1 điều/khoản, hỏi trực tiếp |
| medium | 30 | Nhiều khoản cùng điều, điều kiện, phân biệt trường hợp |
| hard | 25 | Nhiều điều, so sánh, ngoại lệ, suy luận trong tài liệu |
| ood | 20 | Ngoài phạm vi tài liệu — đo **refusal** (25+30+25=80; đủ 100) |

Lưu ý: VBHN ngày 12/02/2026 đã hợp nhất sửa đổi (ví dụ Điều 139 thai sản theo Luật Dân số 113/2025/QH15: sinh con thứ hai nghỉ 07 tháng).

## Chạy

Từ thư mục gốc repo, backend đã ingest PDF:

```bash
python docs/eval/eval_rag.py --mode validate
python docs/eval/eval_rag.py --mode retrieval
python docs/eval/eval_rag.py --mode generation
```

Kết quả index cũ (cắt theo ký tự, 2026-09-20): `generation_full.json` — **60/100**, in-scope 41/80; retrieval `retrieval_baseline.json` — 69/80.

Kết quả sau chunk theo Điều (2026-10-03): `results/both_1790960902.json` — generation **68/100** (in-scope 48/80), retrieval **73/80**.

`--mode retrieval` không cần Ollama. `--mode generation` / `both` cần Ollama (`qwen2.5:3b`).

Checkpoint giữa chừng: `docs/eval/results/generation_checkpoint.json`. Resume:

```bash
python docs/eval/eval_rag.py --mode generation --resume
```

## Metrics

**Retrieval (in-scope)**

- `recall_at_k` — tỷ lệ Điều kỳ vọng xuất hiện trong top-k chunk
- `hit_any` / `hit_all` — tìm được ≥1 / tất cả Điều kỳ vọng
- `mrr` — 1 / hạng chunk đầu tiên chứa Điều kỳ vọng
- PASS retrieval: `hit_any` (câu ood không chấm retrieval)

**Generation**

- `key_fact_coverage` — tỷ lệ `must_contain` có trong câu trả lời (chuẩn hoá không dấu, bỏ số 0 đầu)
- `must_contain_any` — mỗi nhóm cần trúng ≥1 cụm
- `citation_present` / `citation_grounded` — có `[n]` và n nằm trong danh sách nguồn retrieve
- `hallucinated_dieu` — số Điều trong câu trả lời không có trong context retrieve lẫn `expect_dieu`
- `refusal_accuracy` — câu ood có cụm từ chối
- PASS in-scope: coverage ≥ 0.5, không dính `must_not_contain`, có citation
- PASS ood: có refusal

Tái tạo JSON từ source Python (nếu sửa câu hỏi):

```bash
python docs/eval/_build_golden.py
```
