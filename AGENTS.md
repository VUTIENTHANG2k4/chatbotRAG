# ChatbotRAG — Hỏi đáp Pháp luật Lao động Việt Nam

> **AGENT**: Đọc file này đầu mỗi phiên. Cập nhật **Trạng thái hiện tại** và **Recent history** sau mỗi bước.  
> Chi tiết từng bước → [`docs/agent-history/INDEX.md`](docs/agent-history/INDEX.md)

---

## Mục tiêu

Chatbot RAG hỏi đáp pháp luật lao động VN — giúp NLĐ & doanh nghiệp **tra cứu + đối chiếu** quy định HĐLĐ theo tình huống cụ thể. Chỉ trả lời từ tài liệu đã nạp, luôn trích nguồn điều/khoản.

---

## Kiến trúc

| Layer | Công nghệ |
|-------|-----------|
| LLM | Ollama `qwen2.5:3b` (local, 127.0.0.1) |
| Embedding | `keepitreal/vietnamese-sbert` (HuggingFace local) |
| Vector DB | Qdrant file-based |
| Keyword | BM25 → RRF fusion với Qdrant |
| Backend | FastAPI + LangChain · `backend/app/services/rag.py` |
| Frontend | Next.js 14 + Tailwind · `frontend/src/` |

---

## Trạng thái hiện tại

**Cập nhật:** 2026-09-18 · **Giai đoạn:** Phase 2 · **Bước hiện tại:** Bước 5 ⏳ TIẾP THEO

### Kho dữ liệu
- `backend/data/legal_documents/core/18-vbhn-vpqh.pdf` — VBHN Bộ luật Lao động (scan)
- ⚠️ Cần Tesseract + Poppler cài trên máy Windows để OCR file scan

### Checklist chức năng
- [x] RAG pipeline + Hybrid search + Streaming UI hoạt động
- [x] Upload / list / delete tài liệu hoạt động
- [x] AGENTS.md + `.cursor/rules/` thiết lập xong
- [x] Hỗ trợ PDF scan (OCR), DOCX, TXT, ảnh (PNG/JPG/TIFF/BMP/WEBP)
- [x] Scan đệ quy thư mục con trong `data/`
- [x] Auto-ingest khi server khởi động (background thread)
- [x] Endpoint `POST /api/v1/documents/ingest-disk`
- [x] Nhận dạng metadata "Văn bản hợp nhất" (VBHN)
- [x] Retrieval 10/10 PASS, hybrid search hoạt động đúng (Qdrant API fixed)
- [x] System prompt chuyên biệt cho HĐLĐ — cấu trúc 3 phần, 3/3 test PASS
- [x] Câu hỏi gợi ý đúng domain lao động (HĐLĐ)
- [ ] Chưa có filter theo loại văn bản / năm
- [ ] Chưa có chế độ đối chiếu quy định

---

## Lộ trình

| Bước | Tên | Phase | Trạng thái |
|------|-----|-------|-----------|
| 0 | Thiết lập AGENTS.md & rules | 0 | ✅ |
| 1 | Nạp văn bản pháp luật lao động | 1 | ✅ |
| 2 | Kiểm tra retrieval (test set 10 câu) | 1 | ✅ |
| 3 | Tối ưu system prompt HĐLĐ | 2 | ✅ |
| 4 | Cập nhật UI (gợi ý câu hỏi, header) | 2 | ✅ |
| 5 | Bổ sung filter lọc văn bản | 2 | ⏳ |
| 6 | Chế độ đối chiếu quy định | 3 | ⬜ |
| 7 | Metadata hiệu lực văn bản | 3 | ⬜ |
| 8 | Đánh giá & fine-tune (golden set) | 3 | ⬜ |

---

## Recent History (5 bước gần nhất)

| Bước | Ngày | Trạng thái | Tóm tắt | Chi tiết |
|------|------|-----------|---------|---------|
| 0 | 2026-09-18 | ✅ | Tạo AGENTS.md + 5 rule files trong `.cursor/rules/` | [→](docs/agent-history/2026-09/step-00.md) |
| 1 | 2026-09-18 | ✅ | Hỗ trợ PDF scan/ảnh/đệ quy; auto-ingest startup; endpoint /ingest-disk | [→](docs/agent-history/2026-09/step-01.md) |
| 2 | 2026-09-18 | ✅ | 10/10 PASS; fix Qdrant API query_points(); RRF hybrid xác nhận OK | [→](docs/agent-history/2026-09/step-02.md) |
| 3 | 2026-09-18 | ✅ | Prompt HĐLĐ 3 phần; fix localhost→127.0.0.1; đổi 7b→3b; 3/3 PASS | [→](docs/agent-history/2026-09/step-03.md) |
| 4 | 2026-09-18 | ✅ | Cập nhật UI domain HĐLĐ; bộ câu hỏi gợi ý mới; lint/build PASS | [→](docs/agent-history/2026-09/step-04.md) |

> Lịch sử đầy đủ → [`docs/agent-history/INDEX.md`](docs/agent-history/INDEX.md)

---

## Decision Log (ngắn gọn)

| Ngày | Quyết định | Lý do |
|------|-----------|-------|
| 2026-09-18 | Stack local (Ollama + Qdrant) | 100% private, phù hợp dữ liệu pháp luật |
| 2026-09-18 | `vietnamese-sbert` embedding | Tốt nhất cho tiếng Việt pháp lý |
| 2026-09-18 | Chunk theo `Điều/Khoản` | Đơn vị nghĩa pháp lý chuẩn của văn bản VN |
| 2026-09-18 | Tách history → `docs/agent-history/` | Giữ AGENTS.md gọn, tránh nhiễu context |
| 2026-09-18 | `SUPPORTED_EXTS` export từ ingestion.py | Một nguồn sự thật cho danh sách ext hỗ trợ |
| 2026-09-18 | Auto-ingest dùng daemon thread (không async) | ingest_all() là sync + chặn, không dùng asyncio |
| 2026-09-18 | Đổi model 7b → 3b | 7b crash OOM trên máy local; 3b đủ chất lượng cho domain pháp lý |
| 2026-09-18 | OLLAMA_BASE_URL=127.0.0.1 thay vì localhost | localhost→IPv6→Docker/WSL2 intercept; 127.0.0.1→Ollama thật có 3b |

---

## Quy tắc Agent (tóm tắt)

1. Đọc file này + xem `docs/agent-history/INDEX.md` nếu cần chi tiết bước cũ
2. Sau mỗi bước: cập nhật bảng **Recent History** + **Trạng thái hiện tại**, tạo file chi tiết mới
3. Bắt buộc chạy test checklist trước khi đánh dấu bước HOÀN THÀNH (xem `01-workflow.mdc`)
4. KHÔNG xóa dòng nào trong Decision Log
5. Archive: khi Recent History > 5 dòng → xóa dòng cũ nhất (đã có trong INDEX.md)
