FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Optional local background removal (open source). Set INSTALL_LOCAL_AI=1 at build time.
ARG INSTALL_LOCAL_AI=0
RUN if [ "$INSTALL_LOCAL_AI" = "1" ]; then pip install "rembg>=2.0" "onnxruntime>=1.18"; fi

COPY . .

RUN mkdir -p /app/media
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
