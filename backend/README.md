# Backend — Legal RAG API

FastAPI backend for the Vietnamese Legal-Document RAG system.
Defaults to **fully local** stack: Ollama (LLM) + HuggingFace `vietnamese-sbert` (embeddings) + Qdrant local + BM25.

## Tech stack

- **FastAPI** + Uvicorn
- **LangChain** orchestration
- **Qdrant** (file-based local mode) — vector DB
- **rank-bm25** — keyword search
- **Reciprocal Rank Fusion (RRF)** — hybrid search
- **Ollama** — local LLM (`qwen2.5:7b` by default)
- **HuggingFace `keepitreal/vietnamese-sbert`** — Vietnamese embedding (768-dim)

## Folder layout

```
backend/
├── app/
│   ├── main.py                # FastAPI entrypoint
│   ├── api/routes/            # REST endpoints (health, documents, chat)
│   ├── core/                  # config + logging
│   ├── schemas/               # Pydantic request/response models
│   ├── services/              # RAG / hybrid search / ingestion / LLM
│   └── utils/                 # text helpers
├── data/                      # uploaded raw documents
├── storage/
│   ├── vector_db/             # Qdrant local files (auto)
│   └── bm25_index/            # BM25 pickle (auto)
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Setup (local dev)

### 1. Install Ollama and pull a model

```bash
# https://ollama.com/download
ollama pull qwen2.5:7b
ollama serve   # runs on http://localhost:11434
```

### 2. Install Python deps

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate    # Windows
# source .venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux/Mac
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs>

## API endpoints

| Method | Path                          | Description                              |
|--------|-------------------------------|------------------------------------------|
| GET    | `/api/v1/health`              | Service health + index stats             |
| GET    | `/api/v1/health/llm`          | Check Ollama connectivity                |
| GET    | `/api/v1/documents`           | List indexed documents                   |
| POST   | `/api/v1/documents/upload`    | Upload one or more files (PDF/DOCX/TXT)  |
| DELETE | `/api/v1/documents/{source}`  | Remove a document from the index         |
| POST   | `/api/v1/chat`                | Synchronous Q&A (returns full answer)    |
| POST   | `/api/v1/chat/stream`         | Streaming Q&A via Server-Sent Events     |

## Streaming response format (SSE)

The `/chat/stream` endpoint emits these events:

```
event: sources
data: [{"label": "...", "snippet": "...", ...}, ...]

event: token
data: "Theo "

event: token
data: "Bộ luật "

event: done
data: {}
```

## Notes

- The first call may take a while as `sentence-transformers` downloads the embedding model.
- Qdrant runs in **local file-based mode** (no separate server). For higher load, switch to the Qdrant server.
- To enable cloud LLMs, uncomment `langchain-openai` / `langchain-google-genai` in `requirements.txt` and set `LLM_PROVIDER=openai` (or `gemini`) in `.env`.
