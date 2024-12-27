FROM python:3.13-alpine AS builder

# Install `psql` client
RUN apk add --no-cache postgresql-client

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_SYSTEM_PYTHON=1
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# Copy the project into the intermediate image
ADD . /app

# Sync the project
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["python", "-m", "ds_pg_restore.main"]
