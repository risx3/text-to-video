"""FastAPI application entry point."""
from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import jobs as jobs_router
from backend.api.routes import videos as videos_router
from backend.api.websocket.manager import manager
from backend.services import job_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Text-to-Video API",
    description="Generate animated GIFs from text prompts using AnimateDiff on Apple Silicon.",
    version="0.1.0",
)

# ── CORS (dev: allow Vite dev server) ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(jobs_router.router, prefix="/api")
app.include_router(videos_router.router, prefix="/api")


# ── WebSocket — must be at /ws/{job_id} (Vite proxy: /ws → ws://localhost:8000) ─
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(ws: WebSocket, job_id: str):
    job = job_service.get_job(job_id)
    if job is None:
        await ws.close(code=4404)
        return

    await manager.connect(job_id, ws)
    try:
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                if ws.client_state.value == 1:  # CONNECTED
                    await ws.send_text('{"type":"ping"}')
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(job_id, ws)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from backend.core.config import settings

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
