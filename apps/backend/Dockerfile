# Backend image: serves both the API (default CMD) and the worker (command override).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies first (cached layer), then the source.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY worker ./worker
COPY migrations ./migrations
COPY alembic.ini ./

EXPOSE 8000

# Default: API. The worker service overrides this with `python -m worker.main`.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
