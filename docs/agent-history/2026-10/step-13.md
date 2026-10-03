# Bước 13 — Embedding qua Hugging Face Inference

**Ngày:** 2026-10-03
**Trạng thái:** ✅ HOÀN THÀNH
**Phase:** 3

## Mục tiêu bước này

Gọi đúng `keepitreal/vietnamese-sbert` qua API để backend không nạp PyTorch, và vẫn dùng index 768 chiều đã có trên Qdrant Cloud.

## Files thay đổi

| File | Thay đổi |
|---|---|
| `backend/app/services/embeddings.py` | Provider `hf-inference`, L2-normalize |
| `backend/app/core/config.py` | `hf_token` |
| `backend/.env` | `EMBED_PROVIDER=hf-inference` |
| `backend/.env.example` | Ghi hai chế độ embedding |
| `frontend/src/components/ChatPanel.tsx` | Disclaimer khi embedding đi ra ngoài |
| `.cursor/rules/02-backend-rag.mdc` | Quy tắc không đổi model embedding nếu chưa embed lại |

## Quyết định

- Giữ model `keepitreal/vietnamese-sbert`. Không chuyển Gemini Embedding, vì vector khác sẽ làm collection 618 điểm vô dụng.
- `normalize=True` rồi L2-normalize lại phía client cho khớp cosine của index local.

## Test Checklist

| Kiểm tra | Kết quả |
|---|---|
| `EMBED_PROVIDER` đọc thành `hf-inference` | ✅ |
| Chuẩn hóa vector 1 chiều, token tensor, batch | ✅ |
| Gọi Hugging Face Inference | ✅ vector 768 chiều, norm 1.0 |
| So một vector API với vector local | ✅ cosine = 1.0, cùng thứ hạng Qdrant với model trên máy |

## Vấn đề gặp phải

- Không có. Token preset Inference gọi được router Hugging Face.

## Bước tiếp theo gợi ý

- Backend đã không cần nạp PyTorch lúc truy vấn. Có thể deploy image nhẹ lên Render gói 512 MB, frontend trên Vercel.
