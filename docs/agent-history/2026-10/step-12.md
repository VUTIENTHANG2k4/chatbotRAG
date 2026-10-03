# Bước 12 — Cloud Run + Gemini + Qdrant Cloud

**Ngày:** 2026-10-03
**Trạng thái:** ⚠️ CÓ VẤN ĐỀ
**Phase:** 3

## Mục tiêu bước này

Thêm chế độ cloud (Gemini + Qdrant Cloud + Cloud Run) song song với chế độ local, không OCR lại index 618 chunk.

## Files thay đổi

| File | Thay đổi |
|---|---|
| `backend/app/core/config.py` | `qdrant_url`, `qdrant_api_key`, `gemini_model`, `google_api_key`, `auto_ingest`, `enable_admin_api` |
| `backend/app/services/llm.py` | Gemini đọc `settings.gemini_model`, cache, `thinking_level=low` |
| `backend/app/services/vectorstore.py` | Client remote, payload index, `scroll_all_documents()` |
| `backend/app/services/bm25_store.py` | BM25 trong RAM khi Qdrant remote |
| `backend/app/main.py` | Dựng BM25 lúc khởi động; auto-ingest theo cờ |
| `backend/app/api/routes/documents.py` | Upload / ingest-disk / delete trả 403 khi tắt admin API |
| `backend/app/api/routes/health.py` | `/health/llm` báo Gemini |
| `backend/scripts/migrate_to_qdrant_cloud.py` | Copy điểm local sang Qdrant Cloud, so số lượng |
| `backend/Dockerfile`, `backend/entrypoint.sh` | Bake sbert, offline Hub, `PORT`, 1 worker, OCR tùy `INSTALL_OCR` |
| `backend/.env.example`, `docker-compose.yml` | Biến cloud; compose local vẫn Ollama 3b và bật OCR |
| `frontend/src/components/ChatPanel.tsx` | Disclaimer thêm câu xử lý qua AI bên ngoài khi provider không phải Ollama |
| `README.md`, `AGENTS.md`, `.cursor/rules/00`, `.cursor/rules/02` | Hai chế độ local/cloud và lệnh deploy |

## Quyết định

- `QDRANT_URL` rỗng giữ nguyên Qdrant file và BM25 pickle. Có URL thì Cloud Run không ghi đĩa; BM25 dựng từ payload trước khi nhận request.
- Model mặc định `gemini-3.8-flash`. `gemini-2.5-flash` trả 404 với API key hiện tại (Google yêu cầu 3.8).
- `thinking_level=low` vì câu trả lời phải bám đoạn đã retrieve.
- Image production không cài Tesseract/Poppler. Compose local truyền `INSTALL_OCR=true`.
- Admin API tắt trên production. `GET /documents` vẫn mở cho sidebar.

## Test Checklist

| Kiểm tra | Kết quả |
|---|---|
| Compile các module backend đã sửa | ✅ |
| Dry-run migrate: đọc 618 điểm local, upsert sang Qdrant in-memory, BM25 rebuild ra Điều 25 cho câu thử việc | ✅ |
| `python docs/tests/step02_retrieval_test.py` | ✅ 10/10 |
| Golden retrieval (`eval_rag.py --mode both`, cùng index local) | ✅ 73/80, khớp mốc Ollama |
| Golden generation với Gemini | ⚠️ 12 câu gọi được, 10 PASS (có `[1]`, tiếng Việt, coverage 1.0). E01/E02 có trích dẫn nhưng thiếu fact vì retrieval không ra Điều 3 (lỗi cũ). Các câu sau 429: free tier `gemini-3.8-flash` = 20 request/ngày. Checkpoint: `docs/eval/results/generation_checkpoint_gemini.json` |
| Image backend: sbert chạy offline, dim 768 | ✅ |
| Container: health `llm_provider=gemini`, list 200, upload/ingest/delete 403, auto-ingest tắt | ✅ |
| Frontend `tsc --noEmit` | ✅ |
| Migrate thật lên Qdrant Cloud | ✅ 618 điểm local = 618 điểm remote (australia-southeast1) |
| `gcloud run deploy` + smoke URL public | ❌ máy không có `gcloud` |

## Vấn đề gặp phải

- Index đã ở Qdrant Cloud (618/618, region australia-southeast1). Máy dev không có Google Cloud SDK, nên chưa tạo secret và chưa deploy Cloud Run.
- API key Gemini trong `.env` thuộc free tier. Sau khoảng 20 lần `generateContent` với `gemini-3.8-flash`, API trả 429 và bảo retry sau hơn 10 giờ. Bộ 100 câu không chấm hết trong phiên này. Câu đã trả lời cho thấy pipeline Gemini bám format 3 phần và trích `[1]`.
- So với mốc Ollama 68/100: retrieval giữ 73/80 vì cùng vector. Generation chưa có mẫu đủ lớn để so điểm.

## Bước tiếp theo gợi ý

- Cài `gcloud`, làm theo mục "Triển khai Cloud Run" trong README. `QDRANT_URL` trong `.env` đã trỏ cluster Australia. Quota Gemini cần gói trả phí nếu chấm lại 100 câu.
- Chấm lại generation khi hết 429: `python docs/eval/eval_rag.py --mode generation --checkpoint docs/eval/results/generation_checkpoint_gemini.json` sau khi xóa các dòng `error` 429/503 trong checkpoint (nếu không, `--resume` sẽ bỏ qua các câu fail).
- Việc sản phẩm kế tiếp trên lộ trình: Bước 6, chế độ đối chiếu quy định.
