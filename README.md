# Legal RAG — Vietnamese Legal Document Q&A

Production-grade RAG (Retrieval-Augmented Generation) system for Vietnamese legal documents.
**Fully local**: Ollama LLM + HuggingFace embeddings + Qdrant vector DB + BM25 keyword search.

```
┌────────────────────────────┐         ┌────────────────────────┐
│  Next.js 14 Frontend       │  HTTP   │  FastAPI Backend       │
│  (Tailwind, App Router)    │ ◄─────► │  (LangChain, Pydantic) │
└────────────────────────────┘  /api   └───────────┬────────────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          ▼                        ▼                        ▼
                   ┌────────────┐           ┌────────────┐           ┌────────────┐
                   │  Qdrant    │           │   BM25     │           │  Ollama    │
                   │ (vectors)  │           │ (keyword)  │           │ (local LLM)│
                   └────────────┘           └────────────┘           └────────────┘
                          └─────── RRF Fusion ───────┘                      ▲
                                                                            │
                                                              HuggingFace embeddings
```

## Highlights

- **100% local & private** — no API keys required by default
- **Hybrid Search** — Qdrant vector + BM25 keyword fused via Reciprocal Rank Fusion
- **Streaming UI** — token-by-token SSE responses
- **Vietnamese-aware** — chunking by `Chương / Mục / Điều / Khoản`, `vietnamese-sbert` embeddings
- **Source citations** — every answer cites the chunks it used (with snippet + page + RRF score)
- **Pluggable** — swap Ollama for OpenAI / Gemini, or `vietnamese-sbert` for any HF model

## Repo layout

```
chatbotRAG/
├── backend/                # FastAPI service (Python 3.11)
├── frontend/               # Next.js 14 app (TypeScript)
├── docker-compose.yml      # ollama + backend + frontend
└── README.md
```

## Quick start (Docker — recommended)

> **Prerequisites:** Docker Desktop installed. ~10 GB free disk for Ollama + models.

```bash
# 1. Start everything
docker compose up -d --build

# 2. Pull the LLM model into the running Ollama container
docker exec legal-rag-ollama ollama pull qwen2.5:7b

# 3. Open the app
#    Frontend: http://localhost:3000
#    Backend docs: http://localhost:8000/docs
```

To stop:

```bash
docker compose down              # keep data
docker compose down -v           # also wipe volumes (Ollama models, vector_db, etc.)
```

## Local dev (no Docker)

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate         # Windows
# source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
copy .env.example .env           # adjust if needed

# Make sure Ollama is running locally and a model is pulled:
#   ollama pull qwen2.5:7b
#   ollama serve

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
copy .env.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                      # http://localhost:3000
```

## Recommended Ollama models

| Model            | Size  | Quality | Notes                                |
|------------------|-------|---------|--------------------------------------|
| `qwen2.5:7b`     | ~4 GB | High    | Best Vietnamese performance, default |
| `qwen2.5:3b`     | ~2 GB | Good    | Faster, lighter for low RAM          |
| `gemma2:9b`      | ~5 GB | High    | Strong reasoning                     |
| `llama3.1:8b`    | ~5 GB | Good    | Less Vietnamese fluency              |

Change `OLLAMA_MODEL` in `backend/.env` (or `docker-compose.yml`) to switch.

## Hardware

- **Minimum:** 8 GB RAM, no GPU (CPU works but slow)
- **Recommended:** 16 GB RAM + GPU (Ollama uses CUDA / Metal automatically)

## Configuration cheatsheet

Backend `.env` keys (see [backend/.env.example](backend/.env.example) for all):

| Key                  | Default                            | Notes                                |
|----------------------|------------------------------------|--------------------------------------|
| `LLM_PROVIDER`       | `ollama`                           | `ollama` / `openai` / `gemini`       |
| `OLLAMA_MODEL`       | `qwen2.5:7b`                       | Any model pulled in Ollama           |
| `EMBED_PROVIDER`     | `huggingface`                      | `huggingface` / `openai`             |
| `HF_EMBED_MODEL`     | `keepitreal/vietnamese-sbert`      | Any sentence-transformers model      |
| `CHUNK_SIZE`         | `512`                              | Characters per chunk                 |
| `TOP_K`              | `5`                                | Retrieved chunks per query           |
| `RRF_K`              | `60`                               | RRF fusion constant                  |

## API summary

See [backend/README.md](backend/README.md) for full details. Key endpoints:

- `POST /api/v1/documents/upload` — upload PDF/DOCX/TXT
- `GET  /api/v1/documents` — list indexed documents
- `DELETE /api/v1/documents/{source}` — remove a document
- `POST /api/v1/chat/stream` — streaming Q&A (SSE)

## License

MIT
