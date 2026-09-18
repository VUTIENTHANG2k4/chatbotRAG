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
