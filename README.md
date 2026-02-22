# Text-to-Video (AnimateDiff + MLX LLM)

FastAPI + React application that generates short animated GIFs from text prompts.

- Backend: FastAPI, AnimateDiff (`diffusers` + PyTorch), MLX LLM prompt enhancement
- Frontend: React + Vite + Tailwind
- Target hardware: Apple Silicon (`mps`) by default

## Features

- Submit prompt-based video generation jobs
- Background job execution with in-memory job store
- WebSocket progress updates per job
- Optional prompt enhancement using local `mlx-lm`
- Generated GIF download/playback in the UI

## Project Structure

- `backend/`: FastAPI API, job orchestration, model loading
- `frontend/`: React app (Vite) for submitting prompts and viewing results
- `backend/outputs/`: Generated GIFs (created automatically)
- `vite-project/`: Unused starter scaffold (not part of the main app flow)

## Requirements

- macOS on Apple Silicon recommended (default device is `mps`)
- Python 3.11+
- Node.js 18+ (recommended for Vite)
- `uv` for Python dependency management (recommended)

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

- `/api` -> `http://localhost:8000`
- `/ws` -> `ws://localhost:8000`

## Configuration

Backend settings are defined in `backend/core/config.py` and can be overridden via environment variables with the `TTV_` prefix (or `.env` file).

Examples:

```bash
TTV_DEBUG=true
TTV_DEVICE=mps
TTV_PORT=8000
TTV_NUM_FRAMES=8
TTV_NUM_INFERENCE_STEPS=25
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

- `POST /api/jobs` -> create job (returns `202`)
- `GET /api/jobs` -> list jobs
- `GET /api/jobs/{job_id}` -> get job status

Example request:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic drone shot of a waterfall in a jungle",
    "num_frames": 8,
    "num_inference_steps": 25
  }'
```

### WebSocket Progress

- `WS /ws/{job_id}`

The backend broadcasts JSON messages with types:

- `progress`
- `completed`
- `error`
- `ping` (keepalive; frontend ignores)

### Output Files

- `GET /api/videos/{filename}` -> serves generated `.gif` (and supports `.mp4`/`.webm` if present)

## Notes / Limitations

- Job storage is in-memory only (restarts clear job status/history).
- Generated files remain on disk in `backend/outputs/` until manually cleaned.
- First run may take a long time due to model downloads.
- Default generation settings are tuned to reduce Apple Silicon memory pressure.
- No automated tests are currently included.

## Development Checks

```bash
uv run pytest          # currently no tests
uv run ruff check backend frontend
```

## Current Status

- Backend and frontend are wired end-to-end.
- WebSocket progress updates and GIF serving are implemented.
- Root README added; `frontend/README.md` is still the default Vite template.
