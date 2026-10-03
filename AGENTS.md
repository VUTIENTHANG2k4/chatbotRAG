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
| LLM | Local: Ollama `qwen2.5:3b`. Cloud: Gemini `gemini-3.8-flash` |
| Embedding | `keepitreal/vietnamese-sbert`. Local: PyTorch. Cloud nhẹ: Hugging Face Inference (`EMBED_PROVIDER=hf-inference`) |
| Vector DB | Qdrant file-based, hoặc Qdrant Cloud khi có `QDRANT_URL` |
| Keyword | BM25 → RRF. Remote: dựng trong RAM từ payload Qdrant lúc khởi động |
| Backend | FastAPI + LangChain · `backend/app/services/rag.py` |
| Frontend | Next.js 14 + Tailwind · `frontend/src/` |

---

## Trạng thái hiện tại

**Cập nhật:** 2026-10-03 · **Giai đoạn:** Phase 3 · **Bước hiện tại:** Bước 6 ⏳ đối chiếu. Bước 13 xong: embedding qua Hugging Face Inference, cosine 1.0 với index 618 điểm.
### Kho dữ liệu
- `backend/data/legal_documents/core/18-vbhn-vpqh.pdf` — VBHN Bộ luật Lao động (scan), index 618 chunk theo Điều (tái lập 2026-10-02 từ text OCR đã lưu)
- ⚠️ Cần Tesseract + Poppler cài trên máy Windows để OCR file scan
- Golden set sau chunk theo Điều: generation 68/100 (in-scope 48/80), retrieval 73/80 (`docs/eval/results/both_1790960902.json`)

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
- [x] Có filter theo loại văn bản / năm (UI + API + retrieval)
- [x] Golden set 100 câu, chấm lại sau chunk Điều: gen 68/100 (in-scope 48/80); retrieval 73/80
- [x] Chunk theo Điều, heading lặp ở mọi đoạn con; index VBHN đã tái lập (618 chunk)
- [x] Prompt bắt buộc nêu số liệu có trong tài liệu (ngày, giờ, tháng, %, mức tiền)
- [x] Session history sidebar: nhiều phiên, tạo mới, xóa, collapse; lưu localStorage
- [x] Chế độ cloud trong code: Gemini, Qdrant remote, BM25 RAM, tắt admin API, image Cloud Run
- [x] Index 618 điểm đã copy lên Qdrant Cloud (australia-southeast1)
- [x] Provider `hf-inference`: cùng `vietnamese-sbert` qua API, không nạp PyTorch
- [x] Embedding API đã gọi thử: cosine 1.0 với `vietnamese-sbert` local, cùng thứ hạng Qdrant
- [ ] Chưa deploy Cloud Run (thiếu gcloud)
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
| 5 | Bổ sung filter lọc văn bản | 2 | ✅ |
| 6 | Chế độ đối chiếu quy định | 3 | ⏳ |
| 7 | Metadata hiệu lực văn bản | 3 | ⬜ |
| 8 | Đánh giá & fine-tune (golden set) | 3 | ✅ gen 60/100 (index cũ); fine-tune chưa làm |
| 9 | Chunk theo Điều + prompt số liệu | 3 | ✅ index 618 chunk; gen thử việc còn thiếu mức |
| 10 | Chấm lại golden set trên index theo Điều | 3 | ✅ gen 68/100; retrieval 73/80 |
| 11 | Session history sidebar | 3 | ✅ |
| 12 | Cloud Run + Gemini + Qdrant Cloud | 3 | ⚠️ code xong; migrate/deploy/gen 100 chưa chạy được |
| 13 | Embedding qua Hugging Face Inference | 3 | ✅ cosine 1.0 với model local |

---

## Recent History (5 bước gần nhất)

| Bước | Ngày | Trạng thái | Tóm tắt | Chi tiết |
|------|------|-----------|---------|---------|
| 9 | 2026-10-02 | ✅ | Chunk theo Điều; prompt giữ số liệu; tái index 574→618 | [→](docs/agent-history/2026-10/step-09.md) |
| 10 | 2026-10-03 | ✅ | Chấm lại golden set: gen 68/100 (cũ 60); retrieval 73/80 (cũ 69) | [→](docs/agent-history/2026-10/step-10.md) |
| 11 | 2026-10-03 | ✅ | Session history sidebar: nhiều phiên, tạo mới, xóa, collapse; lint+build PASS | [→](docs/agent-history/2026-10/step-11.md) |
| 12 | 2026-10-03 | ⚠️ | Code Cloud Run + Gemini + Qdrant remote; retrieval 73/80; gen Gemini dừng vì quota 20 req/ngày | [→](docs/agent-history/2026-10/step-12.md) |
| 13 | 2026-10-03 | ✅ | Embedding Hugging Face Inference trùng vector local (cosine 1.0) | [→](docs/agent-history/2026-10/step-13.md) |

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
| 2026-09-18 | Filter metadata áp dụng đồng thời cho vector + BM25 | Tránh lệch kết quả retrieval khi chỉ lọc một nhánh |
| 2026-09-20 | Golden set 100 = 25 easy + 30 medium + 25 hard + 20 OOD | 3 nhóm user = 80; OOD cần để đo refusal; không dùng BLEU/ROUGE |
| 2026-09-20 | Gold bám VBHN 18/VBHN-VPQH 12/02/2026 | Có sửa đổi sau 2019 (vd. Điều 139 thai sản con thứ hai = 07 tháng) |
| 2026-10-02 | Cắt chunk đúng theo từng Điều, lặp heading ở mọi đoạn con | Character splitter cắt mất heading; OCR còn dính `lao động.Điều 3` |
| 2026-10-02 | Prompt bắt buộc nêu số liệu nguyên văn, không bịa số | Generation 3b hay bỏ ngày/giờ/% dù context có |
| 2026-10-03 | Thêm chế độ cloud: Gemini + Qdrant Cloud; local giữ khi `QDRANT_URL` rỗng | Cloud Run không có đĩa bền; BM25 dựng lại trong RAM từ payload |
| 2026-10-03 | `GEMINI_MODEL` mặc định `gemini-3.8-flash`, `thinking_level=low` | `gemini-2.5-flash` trả 404 với API key mới; thinking thấp cho RAG bám tài liệu |
| 2026-10-03 | Image production bỏ OCR, bake sbert, 1 worker, tắt admin API | Ingest/OCR chỉ trên máy dev; BM25 trong RAM không chia giữa nhiều worker |
| 2026-10-03 | `EMBED_PROVIDER=hf-inference` gọi đúng `vietnamese-sbert` | Bỏ PyTorch khỏi RAM lúc chạy; vector cùng không gian với index 618 điểm |

---

## Quy tắc Agent (tóm tắt)

1. Đọc file này + xem `docs/agent-history/INDEX.md` nếu cần chi tiết bước cũ
2. Sau mỗi bước: cập nhật bảng **Recent History** + **Trạng thái hiện tại**, tạo file chi tiết mới
3. Bắt buộc chạy test checklist trước khi đánh dấu bước HOÀN THÀNH (xem `01-workflow.mdc`)
4. KHÔNG xóa dòng nào trong Decision Log
5. Archive: khi Recent History > 5 dòng → xóa dòng cũ nhất (đã có trong INDEX.md)
