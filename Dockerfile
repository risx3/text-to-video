# ── Backend Dockerfile ────────────────────────────────────────────────────────
# Targets CPU by default.  For NVIDIA GPU support, use the CUDA base image:
#   docker build --build-arg BASE_IMAGE=pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime .
# and set TTV_DEVICE=cuda in your environment / docker-compose.yml.
#
# Apple Silicon (MPS) cannot be used inside Docker; use the local dev setup instead.

ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE}

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN pip install --no-cache-dir uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies (no apple-silicon extras on Linux/Docker)
# --no-dev skips ruff / pytest so the image stays lean
RUN uv sync --frozen --no-dev

# Copy application source
COPY backend/ backend/

# Ensure the outputs directory exists
RUN mkdir -p backend/outputs

# Default device is CPU; override with -e TTV_DEVICE=cuda for GPU containers
ENV TTV_DEVICE=cpu
ENV TTV_ENABLE_LLM=false

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
