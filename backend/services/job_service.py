"""In-memory job store — no database required."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from backend.schemas.job import Job, JobCreate, JobStatus
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Simple dict-based store; replace with Redis/DB for production
_jobs: dict[str, Job] = {}


def create_job(req: JobCreate) -> Job:
    job = Job(
        prompt=req.prompt,
        num_frames=req.num_frames or settings.num_frames,
        num_inference_steps=req.num_inference_steps or settings.num_inference_steps,
        guidance_scale=req.guidance_scale or settings.guidance_scale,
        width=req.width or settings.width,
        height=req.height or settings.height,
    )
    _jobs[job.job_id] = job
    logger.info("Created job %s", job.job_id)
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def list_jobs() -> list[Job]:
    return sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)


def update_job(job_id: str, **kwargs) -> Optional[Job]:
    job = _jobs.get(job_id)
    if job is None:
        return None
    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)
    job.updated_at = datetime.utcnow()
    return job


def set_status(job_id: str, status: JobStatus, message: str = "") -> Optional[Job]:
    return update_job(job_id, status=status, message=message)


def set_progress(job_id: str, percent: int, message: str = "") -> Optional[Job]:
    return update_job(job_id, progress=percent, message=message)
