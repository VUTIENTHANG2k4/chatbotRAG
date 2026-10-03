# Bước 10 — Chấm lại golden set sau chunk theo Điều

**Ngày:** 2026-10-03
**Trạng thái:** ✅ HOÀN THÀNH
**Phase:** 3

## Mục tiêu bước này

Chấm lại 100 câu trên index đã cắt theo Điều (618 chunk) và so với mốc 2026-09-20.

## Files thay đổi

| File | Thay đổi |
|---|---|
| `docs/eval/results/both_1790960902.json` | Retrieval + generation đầy đủ |
| `docs/eval/results/generation_checkpoint_2026-10-03.json` | Checkpoint lần chấm này |
| `docs/eval/README.md` | Ghi điểm mới cạnh mốc cũ |
| `docs/eval/results/generation_full.json` | Giữ nguyên mốc 2026-09-20 |
| `docs/eval/results/retrieval_baseline.json` | Giữ nguyên mốc 2026-09-20 |

## Quyết định

- Chạy `--mode both`, checkpoint riêng, không `--resume` để không trộn câu trả lời của index cũ.

## Test Checklist

| Kiểm tra | Kết quả |
|---|---|
| Validate 100 câu | ✅ |
| Retrieval 80 câu in-scope | ✅ 73/80 (91%); recall@5=0.874; MRR=0.931 |
| Generation 100 câu, `errors=0` | ✅ 68/100 (68%); in-scope 48/80; OOD 20/20 |
| So với 2026-09-20 | ✅ gen 60→68; retrieval 69→73; hallucination Điều 20%→4% |

## So với mốc cũ

| Nhóm | Retrieval cũ → mới | Generation cũ → mới |
|---|---|---|
| easy | 21/25 → 21/25 | 17/25 → 17/25 |
| medium | 25/30 → 29/30 | 13/30 → 18/30 |
| hard | 23/25 → 23/25 | 11/25 → 13/25 |
| ood | — | 19/20 → 20/20 |
| Tổng | 69/80 → **73/80** | 60/100 → **68/100** |

Generation tăng 13 câu, giảm 5 câu. Tăng: E06, E07, E13, M02, M12, M13, M19, M28, M30, H06, H08, H17, O16. Giảm: E03, E15, E17, M22, H11.

Fail generation còn 32 câu: `must_contain_any_miss` 26, `key_fact_coverage<0.5` 9, `no_citation` 2. Coverage trung bình 0.86. Citation in-scope 97.5%.

Retrieval vẫn fail: E01, E02, E14, E15, M07, H02, H18. E01/E02 vẫn không ra Điều 3 (định nghĩa), dù Điều 2 đã nằm trong top.

## Vấn đề gặp phải

- Câu định nghĩa (“người lao động là gì”) vẫn khớp các đoạn có cụm “người lao động”, không phải Điều 3.
- Cùng một Điều bị cắt nhiều khoản nên top-5 có thể thiếu khoản chứa số. H01 tìm được Điều 35 nhưng câu trả lời không nêu 45/30/3 ngày.
- E06 (12 ngày phép) và E13 (05 ngày Tết) đã PASS.

## Bước tiếp theo gợi ý

- Khi retrieve trúng một Điều, kéo thêm các khoản cùng Điều vào context để model thấy đủ số liệu.
- Riêng câu định nghĩa: ưu tiên chunk có heading “Giải thích từ ngữ” / Điều 3.
- Bước 6 (đối chiếu) vẫn chờ văn bản thứ hai.
