"""Job REST endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.schemas.job import JobCreate, JobResponse, JobStatus, WSMessage, WSMessageType
from backend.api.websocket.manager import manager
from backend.services import job_service
from backend.services.video_service import run_job

logger = logging.getLogger(__name__)

router = APIRouter()


# ── REST ──────────────────────────────────────────────────────────────────────

@router.post("/jobs", response_model=JobResponse, status_code=202)
async def create_job(req: JobCreate, background_tasks: BackgroundTasks):
    """Create a new video generation job and queue it immediately."""
    job = job_service.create_job(req)
    background_tasks.add_task(_run_job_with_ws, job.job_id)
    return job.to_response()


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs():
    """List all jobs, newest first."""
    return [j.to_response() for j in job_service.list_jobs()]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get status of a single job."""
    job = job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_response()


# ── Background task (shared with WS endpoint in main.py) ─────────────────────

async def _run_job_with_ws(job_id: str) -> None:
    """Wrapper that bridges video_service progress callbacks → WebSocket broadcasts."""

    async def on_progress(percent: int, message: str) -> None:
        job = job_service.get_job(job_id)
        if job is None:
            return

        if percent == 100:
            msg = WSMessage(
                type=WSMessageType.completed,
                job_id=job_id,
                percent=100,
                message=message,
                video_url=job.video_url,
                enhanced_prompt=job.enhanced_prompt,
                status=JobStatus.completed,
            )
        elif percent < 0:
            msg = WSMessage(
                type=WSMessageType.error,
                job_id=job_id,
                percent=0,
                message=message,
                error=message,
                status=JobStatus.failed,
            )
        else:
            msg = WSMessage(
                type=WSMessageType.progress,
                job_id=job_id,
                percent=percent,
                message=message,
                status=job.status,
            )

        await manager.broadcast(job_id, msg)

    try:
        await run_job(job_id, on_progress)
    except Exception:
        logger.exception("Background job %s raised an unhandled exception", job_id)
