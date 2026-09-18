# ChatbotRAG — Hỏi đáp pháp luật lao động Việt Nam

Dự án RAG cho tra cứu, đối chiếu và hỏi đáp về quy định lao động Việt Nam bằng tiếng Việt. Hệ thống chạy hoàn toàn cục bộ và ưu tiên dữ liệu pháp luật, với tìm kiếm hybrid giữa vector và từ khóa.

## Tính năng hiện tại

- Tìm kiếm hybrid: Qdrant vector + BM25 keyword qua Reciprocal Rank Fusion (RRF)
- Hỏi đáp streaming theo SSE qua API backend
- Tải lên tài liệu: PDF, DOCX, TXT, PNG, JPG, TIFF, BMP, WEBP
- OCR cho PDF scan / hình ảnh
- Quét đệ quy thư mục dữ liệu và ingest tự động khi khởi động
- Lọc theo loại văn bản và năm trong truy vấn
- Giao diện web Next.js hiển thị danh sách tài liệu, upload, chat và nguồn trích dẫn
- Hỗ trợ metadata như doc_type, year, title và chunk_count

## Kiến trúc

```text
Frontend (Next.js 14)  <--->  FastAPI backend
                                |
                                +--> Qdrant (vector DB)
                                +--> BM25 index (keyword)
                                +--> Ollama (LLM local)
                                +--> HuggingFace sentence-transformers
```

## Stack hiện tại

- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Backend: FastAPI + Pydantic + LangChain
- LLM: Ollama (`qwen2.5:3b` mặc định, đã thay cho 7b để tránh OOM trên máy local)
- Embedding: `keepitreal/vietnamese-sbert`
- Vector database: Qdrant local file-based
- Search: BM25 + RRF
- OCR: Tesseract + Poppler cho file scan/PDF ảnh

## Cấu trúc repo

```text
chatbotRAG/
├── AGENTS.md
├── README.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   ├── data/
│   ├── storage/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── next.config.mjs
│   └── Dockerfile
├── docs/
│   └── agent-history/
├── tests/
└── storage/
```

## Yêu cầu môi trường

- Docker Desktop (nếu chạy theo Docker Compose)
- Python 3.11 cho dev local
- Ollama đã cài đặt và model `qwen2.5:3b` được pull
- Tesseract + Poppler nếu cần OCR PDF scan/ảnh trên Windows

## Chạy nhanh với Docker

```bash
docker compose up -d --build
```

Sau khi khởi động:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Backend port container: `8001:8000` trong Compose

Nếu chưa có model:

```bash
docker exec legal-rag-ollama ollama pull qwen2.5:3b
```

Dừng dịch vụ:

```bash
docker compose down
# hoặc xóa dữ liệu local:
docker compose down -v
```

## Chạy local mà không dùng Docker

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt

# Khởi động Ollama nếu chưa chạy
# ollama serve
# ollama pull qwen2.5:3b

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Mở http://localhost:3000

## Tạo dữ liệu và ingest

Đặt tài liệu vào thư mục `backend/data/` hoặc dùng API upload. Hệ thống có tính năng quét đệ quy và tự ingest khi khởi động.

Các endpoint chính:

- `GET /api/v1/health` — kiểm tra service
- `GET /api/v1/documents` — danh sách tài liệu đã index
- `POST /api/v1/documents/upload` — upload file đơn/lớn
- `POST /api/v1/documents/ingest-disk` — quét toàn bộ thư mục `data/` và nạp lại
- `DELETE /api/v1/documents/{source}` — xóa tài liệu khỏi index
- `POST /api/v1/chat/stream` — hỏi đáp streaming

## Cấu hình quan trọng

Các biến môi trường chính của backend: `LLM_PROVIDER`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `EMBED_PROVIDER`, `HF_EMBED_MODEL`, `HF_DEVICE`, `TOP_K`, `RRF_K`.

Mặc định hiện tại của dự án:

- `OLLAMA_MODEL=qwen2.5:3b`
- `EMBED_PROVIDER=huggingface`
- `HF_EMBED_MODEL=keepitreal/vietnamese-sbert`
- `TOP_K=5`
- `RRF_K=60`

## Lưu ý thực tế

- Thư mục `data/` được quét đệ quy khi backend khởi động; không cần gọi ingest thủ công nếu đã đặt file sẵn.
- Hệ thống hỗ trợ PDF scan / ảnh khi có OCR cài đặt trên máy: Tesseract + Poppler.
- Giao diện hiện tại có sidebar tài liệu, bộ lọc doc_type/year, upload và refresh trạng thái ngay sau khi thay đổi index.
- Dự án tập trung vào pháp luật lao động Việt Nam, nên chunking và prompt đã tối ưu theo domain hiện tại.

## Giấy phép

Mã nguồn dự án được sử dụng theo giấy phép tương ứng của repo; xem chi tiết trong các file hiện có nếu cần công bố chính thức.
