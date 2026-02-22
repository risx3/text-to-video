# Text-to-Video (AnimateDiff-Lightning + MLX LLM)

FastAPI + React application that generates short animated GIFs from text prompts.

- Backend: FastAPI, AnimateDiff-Lightning (`diffusers` + PyTorch), MLX LLM prompt enhancement
- Frontend: React + Vite + Tailwind
- Target hardware: Apple Silicon (`mps`) by default

## Features

- Submit prompt-based video generation jobs
- Background job execution with in-memory job store
- WebSocket progress updates per job
- Optional prompt enhancement using local `mlx-lm`
- Generated GIF download/playback in the UI

## Models

| Component | Model | Notes |
| --------- | ----- | ----- |
| Motion adapter | `ByteDance/AnimateDiff-Lightning` | Distilled; 8-step inference (~3× faster than standard) |
| Base diffusion | `runwayml/stable-diffusion-v1-5` | SD 1.5 at 512×512 |
| Prompt LLM | `mlx-community/Qwen2.5-1.5B-Instruct-4bit` | MLX, Apple Silicon only (~900 MB) |

First run downloads ~4 GB of model weights to the Hugging Face cache.

## Project Structure

- `backend/`: FastAPI API, job orchestration, model loading
- `frontend/`: React app (Vite) for submitting prompts and viewing results
- `backend/outputs/`: Generated GIFs (created automatically)

## Requirements

- macOS on Apple Silicon recommended (default device is `mps`)
- Python 3.11+
- Node.js 18+
- `uv` for Python dependency management

## Quick Start

### 1. Backend

```bash
uv sync
uv run uvicorn backend.main:app --reload
```

API will be available at `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at `http://localhost:5173` and proxies:

- `/api` → `http://localhost:8000`
- `/ws` → `ws://localhost:8000`

## Configuration

Backend settings are in `backend/core/config.py` and can be overridden via environment variables with the `TTV_` prefix (or a `.env` file).

```bash
TTV_DEBUG=true
TTV_DEVICE=mps
TTV_PORT=8000
TTV_NUM_FRAMES=8
TTV_NUM_INFERENCE_STEPS=8        # 4 or 8 for AnimateDiff-Lightning
TTV_GUIDANCE_SCALE=1.0           # keep at 1.0 for Lightning
TTV_LLM_MODEL_ID=mlx-community/Qwen2.5-1.5B-Instruct-4bit
```

Common settings:

- `TTV_HOST`, `TTV_PORT`, `TTV_DEBUG`
- `TTV_DEVICE` (`mps`, `cuda`, `cpu`)
- `TTV_MOTION_ADAPTER_ID`, `TTV_BASE_MODEL_ID`
- `TTV_NUM_FRAMES`, `TTV_WIDTH`, `TTV_HEIGHT`
- `TTV_NUM_INFERENCE_STEPS`, `TTV_GUIDANCE_SCALE`, `TTV_FPS`
- `TTV_LLM_MODEL_ID`, `TTV_LLM_MAX_TOKENS`, `TTV_LLM_TEMP`

## API Overview

### Health

- `GET /health`

### Jobs

- `POST /api/jobs` → create job (returns `202`)
- `GET /api/jobs` → list jobs
- `GET /api/jobs/{job_id}` → get job status

Example request:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic drone shot of a waterfall in a jungle",
    "num_frames": 8,
    "num_inference_steps": 8
  }'
```

> **Lightning note:** `num_inference_steps` should be `4` or `8` to match the distilled checkpoint loaded at startup (set by `TTV_NUM_INFERENCE_STEPS`). Values outside this range will still run but quality may degrade.

### WebSocket Progress

- `WS /ws/{job_id}`

The backend broadcasts JSON messages with types:

- `progress`
- `completed`
- `error`
- `ping` (keepalive; frontend ignores)

### Output Files

- `GET /api/videos/{filename}` → serves generated `.gif`

## Notes / Limitations

- Job storage is in-memory only (restarts clear job status/history).
- Generated files remain on disk in `backend/outputs/` until manually cleaned.
- The Lightning motion adapter is a singleton loaded once at first job. Changing `TTV_NUM_INFERENCE_STEPS` requires a server restart to reload the correct checkpoint.
- `guidance_scale` must stay at `1.0` for AnimateDiff-Lightning; higher values are unsupported by the distilled model.
- No automated tests are currently included.

## Development Checks

```bash
uv run pytest          # currently no tests
uv run ruff check backend frontend
```
