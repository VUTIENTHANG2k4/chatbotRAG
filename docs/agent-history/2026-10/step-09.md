# Bước 9 — Chunk theo Điều và prompt giữ số liệu

**Ngày:** 2026-10-02
**Trạng thái:** ✅ HOÀN THÀNH
**Phase:** 3

## Mục tiêu bước này

Cắt văn bản theo từng Điều, giữ heading ở mọi đoạn con, và bắt prompt nêu đúng số liệu khi tài liệu có. Tái lập index của `18-vbhn-vpqh.pdf` từ text OCR đã lưu.

## Files thay đổi

| File | Thay đổi |
|---|---|
| `backend/app/utils/legal_chunk.py` | Cắt theo Điều; nhận heading OCR dính liền và biến thể `Dieu`/`Điêu` |
| `backend/app/services/ingestion.py` | `chunk_documents()` gọi bộ cắt theo Điều; metadata `dieu`, `dieu_heading` |
| `backend/app/services/rag.py` | Thêm quy tắc giữ nguyên số liệu, không bịa số |
| `backend/app/core/config.py` | Bỏ `VI_SEPARATORS`; `chunk_size` chỉ giới hạn độ dài sau khi đã tách Điều |
| `.cursor/rules/02-backend-rag.mdc` | Mô tả luật cắt mới và prompt số liệu |
| `docs/eval/README.md` | Ghi kết quả 2026-09-20 là index cũ |
| `README.md` | Cập nhật mô tả chunk và prompt |

## Quyết định

- Không gộp hai Điều vào một chunk. Điều dài hơn 512 ký tự thì cắt theo khoản, mỗi đoạn bắt đầu lại bằng `Điều N. ...`.
- Không tách dòng trích dẫn (`Điều 18,`, `Điều này`, `theo Điều 35 của`).
- PDF scan không có text layer. Tái chunk từ corpus BM25 đã OCR (ghép overlap trong từng trang) thay vì OCR lại 86 trang.
- Ví dụ trong prompt không ghi số cụ thể, tránh model 3b chép số ví dụ.

## Test Checklist

| Kiểm tra | Kết quả |
|---|---|
| Syntax `legal_chunk.py`, `ingestion.py`, `rag.py`, `config.py` | ✅ |
| Tách Điều, không gộp, citation không thành điều mới, heading lặp khi Điều dài | ✅ |
| OCR dính `lao động.Điều`, `4Điều`, `Dieu 10` | ✅ |
| Prompt còn quy tắc chỉ trả lời từ tài liệu, từ chối, trích dẫn `[1]`, tiếng Việt, giữ số liệu | ✅ |
| Tái index `18-vbhn-vpqh.pdf` | ✅ 574 → 618 chunk; Qdrant green; BM25 618; 216 số Điều, lớn nhất 220 |
| Retrieval 3 câu (thử việc, phép năm, báo trước) | ✅ top là Điều 25, Điều 113, Điều 35 |
| Generation thử việc nêu đủ 180/60/30/06 | ⚠️ chỉ nêu 06 ngày (khoản 4), dù retrieval ra Điều 25 |
| Generation câu ngoài phạm vi (tuổi nhập ngũ) | ✅ từ chối |

## Vấn đề gặp phải

- `qwen2.5:3b` vẫn bỏ bớt mức số trong cùng một Điều. Câu thử việc chỉ trả khoản 4 (06 ngày), không nêu 180/60/30 dù các đoạn đó có trong index.
- Vài số Điều dưới 220 không tách được vì OCR không có dấu chấm sau số điều. Không OCR lại file trong bước này.
- Kết quả golden set 60/100 là của index cũ. Chưa chạy lại eval.

## Bước tiếp theo gợi ý

- Chạy lại `docs/eval/eval_rag.py` (retrieval rồi generation) trên index mới.
- Bước 6: chế độ đối chiếu, sau khi có văn bản thứ hai (Nghị định 145/2020/NĐ-CP).
