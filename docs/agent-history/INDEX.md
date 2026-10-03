# Agent History — Index

> Lịch sử đầy đủ toàn bộ bước thực hiện.  
> Dashboard hiện tại → [`../../AGENTS.md`](../../AGENTS.md)

---

## Tất cả bước

| Bước | Ngày | Trạng thái | Tên bước | Test pass? | File chi tiết |
|------|------|-----------|---------|-----------|--------------|
| 0 | 2026-09-18 | ✅ HOÀN THÀNH | Thiết lập AGENTS.md & .cursor/rules | N/A (bước setup) | [step-00.md](2026-09/step-00.md) |
| 1 | 2026-09-18 | ✅ HOÀN THÀNH | Nạp văn bản pháp luật + mở rộng ingestion | ✅ code; ⚠️ OCR cần Tesseract | [step-01.md](2026-09/step-01.md) |
| 2 | 2026-09-18 | ✅ HOÀN THÀNH | Kiểm tra retrieval 10 câu; fix Qdrant query_points API | ✅ 10/10 PASS | [step-02.md](2026-09/step-02.md) |
| 3 | 2026-09-18 | ✅ HOÀN THÀNH | Tối ưu system prompt HĐLĐ 3 phần; fix model/URL Ollama | ✅ 3/3 PASS | [step-03.md](2026-09/step-03.md) |
| 4 | 2026-09-18 | ✅ HOÀN THÀNH | Cập nhật UI gợi ý câu hỏi + header theo domain HĐLĐ | ✅ lint/build PASS | [step-04.md](2026-09/step-04.md) |
| 5 | 2026-09-18 | ✅ HOÀN THÀNH | Bổ sung filter doc_type/year (UI + API + hybrid retrieval) | ✅ compile/lint/build PASS | [step-05.md](2026-09/step-05.md) |
| 8 | 2026-09-20 | ✅ HOÀN THÀNH | Golden set 100 câu + chấm generation full | ✅ retrieval 69/80; gen 60/100 | [step-08.md](2026-09/step-08.md) |
| 9 | 2026-10-02 | ✅ HOÀN THÀNH | Chunk theo Điều + prompt giữ số liệu; tái index VBHN | ✅ retrieval 3/3; ⚠️ gen thử việc thiếu mức | [step-09.md](2026-10/step-09.md) |
| 10 | 2026-10-03 | ✅ HOÀN THÀNH | Chấm lại golden set sau chunk theo Điều | ✅ gen 68/100; retrieval 73/80 | [step-10.md](2026-10/step-10.md) |
| 11 | 2026-10-03 | ✅ HOÀN THÀNH | Session history sidebar | ✅ lint/build PASS | [step-11.md](2026-10/step-11.md) |
| 12 | 2026-10-03 | ⚠️ CÓ VẤN ĐỀ | Cloud Run + Gemini + Qdrant Cloud | ⚠️ retrieval 10/10 và 73/80; gen Gemini 10/12 câu gọi được; chưa deploy | [step-12.md](2026-10/step-12.md) |
| 13 | 2026-10-03 | ✅ HOÀN THÀNH | Embedding qua Hugging Face Inference | ✅ cosine 1.0 với model local | [step-13.md](2026-10/step-13.md) |

---

## Hướng dẫn Archive

Khi hoàn thành một bước mới:
1. Thêm một dòng vào bảng trên (đúng thứ tự)
2. Tạo file chi tiết theo đường dẫn `YYYY-MM/step-NN.md`
3. Cập nhật **Recent History** trong `AGENTS.md` (tối đa 5 dòng, xóa dòng cũ nhất nếu tràn)

### Quy ước tên file chi tiết
```
docs/agent-history/
└── YYYY-MM/
    ├── step-00.md
    ├── step-01.md
    └── ...
```
