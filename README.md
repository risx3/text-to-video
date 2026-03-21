# Text-to-Video (AnimateDiff-Lightning)

FastAPI + React application that generates short animated GIFs from text prompts using AnimateDiff-Lightning.

- **Backend:** FastAPI, AnimateDiff-Lightning (`diffusers` + PyTorch), optional MLX LLM prompt enhancement
- **Frontend:** React + Vite + Tailwind
- **Hardware:** CUDA (NVIDIA), Apple Silicon (MPS), or CPU — auto-detected at startup

## Features

- Submit text prompts and generate animated GIFs via background jobs
- Real-time WebSocket progress updates per job
- Optional prompt enhancement using a local LLM (Apple Silicon / `mlx-lm` only)
- Download / playback generated GIFs in the browser

## Models

| Component | Model | Notes |
| --------- | ----- | ----- |
| Motion adapter | `ByteDance/AnimateDiff-Lightning` | Distilled; 4- or 8-step inference |
| Base diffusion | `runwayml/stable-diffusion-v1-5` | SD 1.5 at 512×512 |
| Prompt LLM *(optional)* | `mlx-community/Qwen2.5-1.5B-Instruct-4bit` | Apple Silicon only (~900 MB) |

First run downloads ~4 GB of model weights to the HuggingFace cache (`~/.cache/huggingface`).

## Project Structure

```text
backend/          FastAPI app, job orchestration, model loading
frontend/         React / Vite UI
backend/outputs/  Generated GIFs (created automatically)
Dockerfile        Backend container image
docker-compose.yml  Full-stack Docker Compose setup
.env.example      Annotated environment variable reference
```

## Requirements

| Dependency | Version |
| ---------- | ------- |
| Python | 3.11+ |
| Node.js | 18+ |
| `uv` | latest |

GPU support:

- **NVIDIA:** install PyTorch with the correct CUDA wheel and set `TTV_DEVICE=cuda`
- **Apple Silicon:** works out of the box with `TTV_DEVICE=mps` (default on macOS)
- **CPU:** works everywhere, but generation is slow

---

## Quick Start (local dev)

### 1. Backend

```bash
# Apple Silicon — includes mlx-lm for prompt enhancement
uv sync --extra apple-silicon

# All other platforms (CUDA or CPU)
uv sync

uv run uvicorn backend.main:app --reload
```

API available at `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:5173`. Proxies:

- `/api` → `http://localhost:8000`
- `/ws`  → `ws://localhost:8000`

---

## Docker

### CPU (default)

```bash
docker compose up --build
```

- Backend at `http://localhost:8000`
- Frontend dev server at `http://localhost:5173`
- Generated GIFs persisted to `./backend/outputs/`
- HuggingFace model cache persisted in a named Docker volume

### NVIDIA GPU

1. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).
2. Uncomment the `deploy` block in `docker-compose.yml`.
3. Run:

```bash
TTV_DEVICE=cuda docker compose up --build
```

### Apple Silicon (MPS)

MPS acceleration cannot be passed through to Docker containers on macOS.
Use the **local dev** setup above for MPS; Docker is CPU-only on Mac.

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed. All variables use the `TTV_` prefix and can also be passed directly as environment variables.

```bash
cp .env.example .env
```

### Key variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `TTV_DEVICE` | `auto` | `auto` \| `cuda` \| `mps` \| `cpu` |
| `TTV_NUM_FRAMES` | `8` | Frames per GIF (4–64) |
| `TTV_NUM_INFERENCE_STEPS` | `8` | Must be `4` or `8` for Lightning |
| `TTV_GUIDANCE_SCALE` | `1.0` | Keep at `1.0` for AnimateDiff-Lightning |
| `TTV_FPS` | `8` | Output GIF frame rate |
| `TTV_ENABLE_LLM` | `true` | Set `false` to skip prompt enhancement |
| `TTV_LLM_MODEL_ID` | `mlx-community/Qwen2.5-1.5B-Instruct-4bit` | MLX LLM (Apple Silicon only) |
| `TTV_DEBUG` | `false` | Enable Uvicorn auto-reload |

See `.env.example` for the full list.

---

## API

### Health

```http
GET /health
→ {"status": "ok", "device": "cuda"}
```

### Jobs

```http
POST /api/jobs          Create a job (returns 202)
GET  /api/jobs          List all jobs (newest first)
GET  /api/jobs/{id}     Get job status
```

Example:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic drone shot of a waterfall in a jungle",
    "num_frames": 8,
    "num_inference_steps": 8
  }'
```

> **Lightning note:** `num_inference_steps` must match the checkpoint loaded at startup (`TTV_NUM_INFERENCE_STEPS`). Supported values: `4` or `8`. Changing this setting requires a server restart.

### WebSocket progress

```http
WS /ws/{job_id}
```

Message types broadcast by the server:

| Type | When |
| ---- | ---- |
| `progress` | Each inference step (percent 0–99) |
| `completed` | Job finished; includes `video_url` |
| `error` | Job failed; includes `error` message |
| `ping` | Keepalive (ignore) |

### Output files

```http
GET /api/videos/{filename}   Serve generated .gif
```

---

## Notes / Limitations

- **Job storage is in-memory only** — all job history is lost on server restart.
- **Generated files remain on disk** in `backend/outputs/` until manually deleted.
- **Changing `TTV_NUM_INFERENCE_STEPS` requires a server restart** to load the matching Lightning checkpoint.
- **`guidance_scale` must be `1.0`** for AnimateDiff-Lightning; higher values produce degraded output.
- **Prompt enhancement requires Apple Silicon** and the `apple-silicon` extra (`uv sync --extra apple-silicon`). On other platforms `TTV_ENABLE_LLM` is automatically treated as `false`.
- No automated tests are currently included.

## Development Checks

```bash
uv run ruff check backend
uv run pytest          # no tests yet
```
