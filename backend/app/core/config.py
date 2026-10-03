from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Centralized application settings (loaded from .env)."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "Legal RAG API"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    # Optional regex so a Vercel frontend can call this API from the browser.
    # Example: https://.*\.vercel\.app
    cors_origin_regex: str = ""

    # ── LLM (default: Ollama local) ──────────────────────────────────────
    llm_provider: str = "ollama"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"
    # gemini-2.5-flash returns 404 for new API keys; Google points those keys at 3.8.
    gemini_model: str = "gemini-3.8-flash"
    # Loaded from GOOGLE_API_KEY so a local .env works the same as Cloud Run env.
    google_api_key: str = ""

    # ── Embeddings (default: HuggingFace local) ──────────────────────────
    # huggingface = local sentence-transformers. hf-inference = same model via API.
    embed_provider: str = "huggingface"
    hf_embed_model: str = "keepitreal/vietnamese-sbert"
    hf_device: str = "cpu"
    hf_token: str = ""

    # ── Storage paths ─────────────────────────────────────────────────────
    data_dir: Path = BASE_DIR / "data"
    qdrant_path: Path = BASE_DIR / "storage" / "vector_db"
    bm25_index_path: Path = BASE_DIR / "storage" / "bm25_index"
    qdrant_collection: str = "legal_documents"
    # Empty = file-based Qdrant at qdrant_path. Set to use Qdrant Cloud/server;
    # BM25 is then rebuilt in memory from Qdrant payloads instead of pickle files.
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # ── Deployment ────────────────────────────────────────────────────────
    auto_ingest: bool = True
    enable_admin_api: bool = True

    # ── Chunking ──────────────────────────────────────────────────────────
    # Primary split is by Điều (see app.utils.legal_chunk). These bound a piece
    # after the heading is repeated on every sub-chunk of a long article.
    chunk_size: int = 512
    chunk_overlap: int = 50

    # ── Retrieval ─────────────────────────────────────────────────────────
    top_k: int = 5
    rrf_k: int = 60

    # ── Upload limits ─────────────────────────────────────────────────────
    max_upload_size_mb: int = 50

    @property
    def use_remote_qdrant(self) -> bool:
        return bool(self.qdrant_url.strip())

    def ensure_dirs(self) -> None:
        dirs = [self.data_dir]
        if not self.use_remote_qdrant:
            dirs += [self.qdrant_path, self.bm25_index_path]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
