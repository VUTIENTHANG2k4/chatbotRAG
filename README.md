# ChatbotRAG — Hỏi đáp pháp luật lao động Việt Nam

Dự án RAG cho tra cứu, đối chiếu và hỏi đáp về quy định lao động Việt Nam bằng tiếng Việt. Chế độ mặc định chạy cục bộ (Ollama + Qdrant file). Chế độ cloud dùng Gemini và Qdrant Cloud: câu hỏi cùng đoạn luật được retrieve sẽ gửi tới Google.

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
                                +--> Qdrant local hoặc Qdrant Cloud
                                +--> BM25 (pickle local, hoặc RAM khi dùng Qdrant Cloud)
                                +--> Ollama (local) hoặc Gemini (cloud)
                                +--> HuggingFace sentence-transformers
```

## Stack hiện tại

- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Backend: FastAPI + Pydantic + LangChain
- LLM local: Ollama (`qwen2.5:3b`). LLM cloud: Gemini `gemini-3.8-flash`
- Embedding: `keepitreal/vietnamese-sbert` (cả hai chế độ)
- Vector database: Qdrant local file-based, hoặc Qdrant Cloud khi có `QDRANT_URL`
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
- Chunk theo từng Điều (heading được lặp ở mọi đoạn con). Prompt bắt buộc nêu đúng số ngày, giờ, tháng, phần trăm và mức tiền khi tài liệu có ghi.

## Triển khai miễn phí (Render + Vercel)

Image local (`backend/Dockerfile`) vẫn cài PyTorch để chạy `EMBED_PROVIDER=huggingface`. Gói Render Free chỉ có 512 MB RAM, nên production nhẹ dùng `backend/Dockerfile.cloud` và `backend/requirements-cloud.txt`: không torch, embedding qua Hugging Face Inference, LLM Gemini, Qdrant Cloud. `render.yaml` khai báo service Free ở Singapore. Secret (`GOOGLE_API_KEY`, `HF_TOKEN`, `QDRANT_URL`, `QDRANT_API_KEY`) đặt trên dashboard, không ghi vào git.

Frontend trên Vercel đặt `NEXT_PUBLIC_BACKEND_ORIGIN` bằng URL Render (không có `/api/v1`). Trình duyệt gọi API trực tiếp. Backend cần `CORS_ORIGIN_REGEX=https://.*\.vercel\.app`. Local vẫn đi qua `/api/backend`.

Đang chạy:

- Giao diện: `https://legal-rag-three.vercel.app`
- API: `https://legal-rag-backend-z8am.onrender.com` (Render Free, Singapore)

Máy API ngủ sau khoảng 15 phút không có request; lần gọi đầu sau đó mất khoảng một phút.

## Triển khai Cloud Run

Qdrant Cloud là nguồn sự thật. Cloud Run không giữ index trên đĩa: lúc khởi động backend kéo payload về và dựng BM25 trong RAM. Lịch sử phiên vẫn ở `localStorage` của trình duyệt. OCR và ingest chỉ làm trên máy dev; image production không cài Tesseract/Poppler.

Việc chưa làm được trên máy này nếu thiếu tool: cài [Google Cloud SDK](https://cloud.google.com/sdk/docs/install), `gcloud auth login`, và một cluster Qdrant Cloud (region gần `asia-southeast1`).

### 1. Đẩy 618 điểm local lên Qdrant Cloud

Dừng backend local trước (Qdrant file chỉ cho một client). Chạy từ `backend/`:

```bash
set QDRANT_URL=https://YOUR-CLUSTER.cloud.qdrant.io
set QDRANT_API_KEY=YOUR_KEY
python scripts/migrate_to_qdrant_cloud.py
```

Script in số điểm hai bên. Lệch số thì dừng, không deploy. `--recreate` xóa collection remote trước khi copy.

### 2. Secret và backend

```bash
gcloud config set project YOUR_PROJECT
gcloud services enable run.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# dán key rồi Ctrl+Z / Ctrl+D
gcloud secrets create google-api-key --replication-policy=automatic --data-file=-
gcloud secrets create qdrant-api-key --replication-policy=automatic --data-file=-

gcloud run deploy legal-rag-backend \
  --source backend \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --cpu 2 --memory 4Gi \
  --min-instances 1 --concurrency 10 --timeout 300 \
  --set-env-vars "LLM_PROVIDER=gemini,GEMINI_MODEL=gemini-3.8-flash,EMBED_PROVIDER=huggingface,HF_EMBED_MODEL=keepitreal/vietnamese-sbert,HF_DEVICE=cpu,QDRANT_URL=https://YOUR-CLUSTER.cloud.qdrant.io,QDRANT_COLLECTION=legal_documents,AUTO_INGEST=false,ENABLE_ADMIN_API=false" \
  --set-secrets "GOOGLE_API_KEY=google-api-key:latest,QDRANT_API_KEY=qdrant-api-key:latest"
```

Image đã bake `vietnamese-sbert` (`HF_HUB_OFFLINE=1`) và đọc `PORT`. Một worker uvicorn.

### 3. Frontend

`BACKEND_URL` là biến server, rewrite `/api/backend/*` lúc chạy.

```bash
gcloud run deploy legal-rag-frontend \
  --source frontend \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars "BACKEND_URL=https://BACKEND_URL,HOSTNAME=0.0.0.0"
```

Rồi cập nhật CORS của backend cho đúng URL frontend:

```bash
gcloud run services update legal-rag-backend --region asia-southeast1 \
  --update-env-vars "CORS_ORIGINS=[\"https://FRONTEND_URL\"]"
```

### 4. Smoke test sau deploy

- `GET /api/v1/health` → `total_chunks` = 618, `llm_provider` = `gemini`
- `POST /api/v1/documents/upload` → 403
- Hỏi 3 câu trên UI; footer vẫn có disclaimer, và thêm câu câu hỏi được xử lý qua dịch vụ AI bên ngoài
- Câu ngoài phạm vi bị từ chối; câu trả lời tiếng Việt và có `[1]`, `[2]`

Biến production: `LLM_PROVIDER`, `GEMINI_MODEL`, `GOOGLE_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `AUTO_INGEST=false`, `ENABLE_ADMIN_API=false`, `CORS_ORIGINS`, `BACKEND_URL`.

## Giấy phép

Mã nguồn dự án được sử dụng theo giấy phép tương ứng của repo; xem chi tiết trong các file hiện có nếu cần công bố chính thức.
