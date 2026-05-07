FROM python:3.13-slim


ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for better caching
COPY pyproject.toml .

# Install only runtime deps
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system .

COPY . .

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
