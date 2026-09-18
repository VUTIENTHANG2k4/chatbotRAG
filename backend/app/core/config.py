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

    # ── LLM (default: Ollama local) ──────────────────────────────────────
    llm_provider: str = "ollama"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"

    # ── Embeddings (default: HuggingFace local) ──────────────────────────
    embed_provider: str = "huggingface"
    hf_embed_model: str = "keepitreal/vietnamese-sbert"
    hf_device: str = "cpu"

    # ── Storage paths ─────────────────────────────────────────────────────
    data_dir: Path = BASE_DIR / "data"
    qdrant_path: Path = BASE_DIR / "storage" / "vector_db"
    bm25_index_path: Path = BASE_DIR / "storage" / "bm25_index"
    qdrant_collection: str = "legal_documents"

    # ── Chunking ──────────────────────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 50

    # ── Retrieval ─────────────────────────────────────────────────────────
    top_k: int = 5
    rrf_k: int = 60

    # ── Upload limits ─────────────────────────────────────────────────────
    max_upload_size_mb: int = 50

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.qdrant_path, self.bm25_index_path):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()


# Vietnamese-aware text splitter separators (ordered from largest to smallest unit)
VI_SEPARATORS = [
    "\n\nChương ",
    "\n\nMục ",
    "\n\nĐiều ",
    "\n\nKhoản ",
    "\n\n",
    "\n",
    " ",
    "",
]
