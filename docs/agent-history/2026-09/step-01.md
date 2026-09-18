# Bước 1 — Nạp văn bản pháp luật lao động & mở rộng ingestion pipeline

**Ngày:** 2026-09-18  
**Trạng thái:** ✅ HOÀN THÀNH  
**Phase:** 1 — Dữ liệu & Kiểm thử cơ bản

---

## Mục tiêu bước này

- Hỗ trợ PDF scan (ảnh), file ảnh trực tiếp (PNG/JPG/TIFF/...), quét đệ quy thư mục con
- Auto-ingest khi server khởi động
- Thêm endpoint `/ingest-disk` để trigger thủ công
- Nhận dạng metadata "Văn bản hợp nhất" (VBHN) từ tên file

## File đã thêm vào kho dữ liệu

| File | Loại | Ghi chú |
|------|------|---------|
| `backend/data/legal_documents/core/18-vbhn-vpqh.pdf` | PDF scan (ảnh) | VBHN Bộ luật Lao động 2019 — cần OCR |

## Files thay đổi code

| File | Thay đổi |
|------|---------|
| `backend/app/utils/text.py` | Thêm pattern `"Văn bản hợp nhất": r"\bvbhn\b"` vào `_DOC_TYPE_PATTERNS` |
| `backend/requirements.txt` | Thêm `Pillow>=10.0.0` |
| `backend/app/services/ingestion.py` | Thêm `_IMAGE_EXTS`, `SUPPORTED_EXTS`; thêm `load_image()`; sửa `load_document()`; sửa `ingest_all()` dùng `rglob()` |
| `backend/app/api/routes/documents.py` | `_ALLOWED_EXTS = SUPPORTED_EXTS`; thêm `POST /ingest-disk` endpoint; bỏ import trùng `settings` |
| `backend/app/main.py` | Thêm `_startup_ingest()` chạy trong daemon thread sau 3 giây startup |

## Quyết định

- `SUPPORTED_EXTS` được export từ `ingestion.py` → một nguồn sự thật duy nhất cho cả ingestion và API
- Dùng `daemon thread` (không phải asyncio task) vì `ingest_all()` là blocking sync
- `time.sleep(3)` trước khi auto-ingest để Qdrant collection init xong trước

## Yêu cầu hệ thống để OCR hoạt động (Windows local)

Nếu không dùng Docker, cần cài thủ công:
1. **Tesseract OCR for Windows**: https://github.com/UB-Mannheim/tesseract/wiki  
   - Trong trình cài, tick chọn "Vietnamese" language pack
2. **Poppler for Windows** (cho `pdf2image`): https://github.com/oschwartz10612/poppler-windows/releases  
   - Giải nén và thêm thư mục `bin/` vào PATH
3. Sau đó: `pip install pytesseract Pillow pdf2image`

Nếu chạy Docker: Tesseract + Poppler đã được cài sẵn trong Dockerfile.

## Test Checklist

| Kiểm tra | Kết quả |
|---------|---------|
| `SUPPORTED_EXTS` export được từ `ingestion.py` | ✅ |
| `load_image()` có import guard + error logging | ✅ |
| `ingest_all()` dùng `rglob()` thay `iterdir()` | ✅ |
| `POST /ingest-disk` endpoint có trong router | ✅ |
| `_ALLOWED_EXTS` trong documents.py dùng `SUPPORTED_EXTS` | ✅ |
| `_startup_ingest` là daemon thread (không block shutdown) | ✅ |
| Pattern `vbhn` trong `_DOC_TYPE_PATTERNS` | ✅ |
| `Pillow` trong requirements.txt | ✅ |
| ⚠️ OCR thực tế với file PDF scan | Phụ thuộc Tesseract có cài không |

## Vấn đề gặp phải

- File `18-vbhn-vpqh.pdf` là PDF scan (ảnh), KHÔNG có text layer → bắt buộc phải có Tesseract
- Nếu Tesseract chưa cài: ingestion sẽ trả về `"empty_document"` — server log sẽ có warning rõ
- Trên Windows: cần thêm đường dẫn Tesseract vào PATH hoặc set `pytesseract.pytesseract.tesseract_cmd`

## Bước tiếp theo (Bước 2)

Sau khi server chạy và file được index thành công, chạy test set 10 câu hỏi đại diện:
- Dùng giao diện chat hoặc `POST /api/v1/chat`
- Kiểm tra source trả về có đúng trang/điều không
- Nếu OCR kém → xem xét tăng DPI (hiện 300) hoặc tiền xử lý ảnh
