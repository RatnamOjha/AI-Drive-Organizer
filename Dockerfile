# ── Base image ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: Tesseract for OCR
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 && \
    rm -rf /var/lib/apt/lists/*

# ── Dependencies ────────────────────────────────────────────────────────────
FROM base AS deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ── Application ─────────────────────────────────────────────────────────────
FROM deps AS app

# Copy source
COPY src/ ./src/
COPY assets/ ./assets/
COPY config.example.yaml ./config.example.yaml

# Non-root user for security
RUN useradd -m -u 1000 organizer && \
    mkdir -p credentials reports && \
    chown -R organizer:organizer /app
USER organizer

# Volume mount point for credentials and reports
VOLUME ["/app/credentials", "/app/reports"]

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--help"]
