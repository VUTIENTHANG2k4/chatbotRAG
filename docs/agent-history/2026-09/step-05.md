# Bước 5 — Bổ sung filter theo loại văn bản / năm

**Ngày:** 2026-09-18  
**Trạng thái:** ✅ HOÀN THÀNH  
**Phase:** 2

## Mục tiêu bước này
Cho phép người dùng lọc ngữ cảnh RAG theo `loại văn bản` và `năm` ngay trên UI chat, sau đó truyền filter xuống backend để áp dụng cho cả vector search và BM25.

## Files thay đổi
| File | Thay đổi |
|---|---|
| `backend/app/schemas/chat.py` | Thêm field `filter_doc_type`, `filter_year` vào `ChatRequest` |
| `backend/app/api/routes/chat.py` | Thêm `_build_filter_metadata()` và truyền filter vào `ask()` / `ask_stream_async()` |
| `backend/app/services/bm25_store.py` | Thêm lọc metadata cho BM25 (`_matches_filter`) |
| `backend/app/services/hybrid_search.py` | Truyền `filter_metadata` vào `bm25_search()` để hybrid filter đồng nhất |
| `frontend/src/lib/api.ts` | Mở rộng payload stream chat gửi `filter_doc_type`, `filter_year` |
| `frontend/src/components/ChatPanel.tsx` | Thêm 2 dropdown filter (loại VB, năm), load option từ `listDocuments()`, gửi filter khi hỏi |
| `frontend/.env.local` | Thêm `BACKEND_URL=http://127.0.0.1:8000` cho rewrite local ổn định |
| `frontend/next.config.mjs` | Giữ rewrite `/api/backend/*` với fallback local `127.0.0.1` và `beforeFiles` |

## Quyết định
- Áp dụng filter cho cả **vector** và **BM25** trước khi RRF để tránh lệch kết quả giữa 2 nhánh retrieval.
- Lấy option filter từ tài liệu đã index (`listDocuments`) thay vì hard-code để UI tự thích nghi theo kho dữ liệu.
- Giữ chuẩn frontend gọi API qua `API_BASE="/api/backend"`; không gọi trực tiếp backend URL trong client.

## Test Checklist
| Kiểm tra | Kết quả |
|---|---|
| File mới/sửa không có lỗi import / syntax (Backend) | ✅ `python -m compileall app` PASS |
| API endpoint trả về đúng schema (Backend) | ✅ `POST /api/v1/chat` với `filter_doc_type` trả `200`, có `sources` |
| Không làm hỏng endpoint hiện có (health, documents, chat) | ✅ `health/documents/chat/stream` đều trả đúng trạng thái |
| Logger dùng get_logger(__name__), không dùng print() | ✅ Không thay đổi logger sai quy ước |
| Có type hints đầy đủ | ✅ Các hàm mới có type hints |
| Không có TypeScript error (Frontend) | ✅ `npm run build` PASS |
| Component render đúng với dữ liệu mẫu | ✅ build thành công, dropdown filter render từ API |
| API call dùng đúng `API_BASE = "/api/backend"` | ✅ Đã giữ/khôi phục |
| Disclaimer pháp lý vẫn còn ở footer input | ✅ Vẫn còn trong `ChatPanel.tsx` |
| SUGGESTED_QUESTIONS đúng domain HĐLĐ | ✅ Giữ nguyên từ bước 4 |

## Vấn đề gặp phải
- Trong quá trình test, tồn tại nhiều process backend cũ làm Qdrant local bị lock (`already accessed by another instance`).
- Đã xử lý bằng cách dọn process backend mồ côi và chạy 1 backend instance ổn định.

## Bước tiếp theo gợi ý
- Bước 6: Chế độ đối chiếu quy định (so sánh 2 nguồn/2 điều luật trong cùng câu trả lời).
