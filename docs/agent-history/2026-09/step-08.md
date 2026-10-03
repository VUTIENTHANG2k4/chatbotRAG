# Bước 8 — Golden set 100 câu + chấm generation

**Ngày:** 2026-09-20
**Trạng thái:** ✅ HOÀN THÀNH
**Phase:** 3

## Mục tiêu bước này

Tạo golden set 100 câu bám `18-vbhn-vpqh.pdf` và chấm câu trả lời chatbot (`qwen2.5:3b` + hybrid RAG) trên toàn bộ dataset. Chưa fine-tune model.

## Files thay đổi

| File | Thay đổi |
|---|---|
| `docs/eval/golden_set.json` | Dataset 100 câu |
| `docs/eval/_build_golden.py` | Source tái tạo JSON |
| `docs/eval/eval_rag.py` | Script chấm + checkpoint từng câu |
| `docs/eval/README.md` | Hướng dẫn chạy |
| `docs/eval/results/retrieval_baseline.json` | Baseline retrieval |
| `docs/eval/results/generation_full.json` | Kết quả generation 100 câu |

## Quyết định

- 100 câu = 25 easy + 30 medium + 25 hard + 20 OOD (refusal).
- Không dùng BLEU/ROUGE. PASS generation in-scope: key-fact ≥ 50%, không dính `must_not_contain`, có citation.
- Gold bám VBHN 2026 (Điều 139: sinh con thứ hai = 07 tháng).

## Test Checklist

| Kiểm tra | Kết quả |
|---|---|
| Schema 100 câu (25/30/25/20) | ✅ |
| Retrieval 100 câu | ✅ 69/80 in-scope (86%); recall@5=0.779; MRR=0.770 |
| Generation 100 câu qua Ollama `qwen2.5:3b` | ✅ 60/100 (60%); in-scope 41/80 (51%); OOD 19/20 (95%) |
| Không lỗi API/exception trên 100 câu | ✅ `errors=0` |
| Citation present in-scope | ✅ 98.75% |
| Citation grounded in-scope | ✅ 97.5% |

## Generation — kết quả chính

| Nhóm | PASS | Ghi chú |
|---|---|---|
| easy | 17/25 (68%) | Sai định nghĩa (E01/E02), thiếu số ngày phép/Tết |
| medium | 13/30 (43%) | Thiếu số liệu hoặc nhầm Điều |
| hard | 11/25 (44%) | So sánh nhiều Điều; hay nêu đúng 1 nhánh |
| ood | 19/20 (95%) | O16 bịa Luật NVQS |
| **Tổng** | **60/100** | Key-fact coverage trung bình 0.78 |
| In-scope only | **41/80 (51%)** | Điểm chất lượng HĐLĐ thực tế |

Nguyên nhân FAIL (40 câu; một câu có thể nhiều lý do):

- `must_contain_any_miss`: 32
- `key_fact_coverage<0.5`: 15
- `no_citation`: 1 (H03)
- `no_refusal`: 1 (O16)
- `hallucinated_dieu_rate`: 20%

Lỗi pháp lý thật (không chỉ matcher chặt):

- E02: nhầm đối tượng áp dụng (Điều 2) với định nghĩa NSDLĐ (Điều 3)
- E06: không nêu 12 ngày phép điều kiện bình thường
- E13: không nêu 05 ngày Tết Âm lịch
- M02: dẫn Điều 22/23 thay vì Điều 20 khoản 2
- M07: dẫn Điều 39 thay vì Điều 37
- O16: bịa độ tuổi nhập ngũ, không từ chối

## Retrieval baseline (in-scope)

easy 21/25 · medium 25/30 · hard 23/25. FAIL: E01, E02, E04, E14, M02, M07, M17, M21, M22, H16, H23.

## Vấn đề gặp phải

- OCR + chunk cắt heading Điều → retrieval/definition yếu (E01, E02).
- Model 3b giữ format 3 phần và citation tốt, nhưng hay thiếu số liệu và nhầm Điều khi multi-hop.
- Một số FAIL do matcher AND quá chặt (vd. E21 trả đúng 01/01/2021).

## Bước tiếp theo gợi ý

- Chunk theo Điều, giữ heading trong mọi chunk.
- Prompt: bắt buộc nêu số liệu (ngày/giờ/%) khi tài liệu có.
- Quay lại Bước 6: chế độ đối chiếu quy định.
