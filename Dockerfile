# FinBot — multi-stage Docker build (FastAPI + React)

# --- Stage 1: Build frontend ---
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# --- Stage 2: Install Python dependencies ---
FROM python:3.12-slim AS backend-builder
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml ./
COPY src/ src/
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# --- Stage 3: Runtime ---
FROM python:3.12-slim
WORKDIR /app

COPY --from=backend-builder /app/.venv /app/.venv
COPY --from=backend-builder /app/src /app/src
COPY --from=backend-builder /app/pyproject.toml /app/pyproject.toml
COPY --from=frontend-builder /app/frontend/.output/public /app/static
COPY alembic.ini ./
COPY scripts/ scripts/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    FINBOT_OLLAMA_HOST="http://ollama:11434" \
    FINBOT_KEY_DIR="/app/data/.keys" \
    FINBOT_DATA_DIR="/app/data" \
    FINBOT_WATCH_FOLDER="/app/finbot-inbox"

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/docs')" || exit 1

CMD ["uvicorn", "finbot.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
