FROM python:3.11-slim AS base

# INSTALL_OCR=true for local images that ingest scanned PDFs; Cloud Run images
# never ingest (index is migrated offline), so the default leaves OCR out.
ARG INSTALL_OCR=false
ARG HF_EMBED_MODEL=keepitreal/vietnamese-sbert

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/hf \
    HF_EMBED_MODEL=${HF_EMBED_MODEL}

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && if [ "$INSTALL_OCR" = "true" ]; then \
        apt-get install -y --no-install-recommends \
            tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng poppler-utils; \
    fi \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Install torch CPU-only first (avoids downloading ~2 GB of CUDA libraries)
RUN pip install --upgrade pip \
    && pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# Bake the embedding model into the image so cold starts don't hit HuggingFace.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${HF_EMBED_MODEL}')"
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY ./app ./app
COPY ./scripts ./scripts
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/data /app/storage/vector_db /app/storage/bm25_index

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/api/v1/health || exit 1

# Single worker: BM25 lives in process memory and is rebuilt per instance.
# PORT is expanded in entrypoint.sh so Cloud Run can override it.
CMD ["/entrypoint.sh"]
