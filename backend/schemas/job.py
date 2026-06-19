from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    pending = "pending"
    enhancing = "enhancing"
    generating = "generating"
    completed = "completed"
    failed = "failed"


# ── Request / Response models ─────────────────────────────────────────────────

class JobCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="User text prompt")
    num_frames: Optional[int] = Field(None, ge=4, le=128)
    num_inference_steps: Optional[int] = Field(None, ge=1, le=100)
    guidance_scale: Optional[float] = Field(None, ge=1.0, le=20.0)
    width: Optional[int] = Field(None, ge=256, le=1024)
    height: Optional[int] = Field(None, ge=256, le=1024)


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    prompt: str
    enhanced_prompt: Optional[str] = None
    progress: int = 0
    message: str = ""
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ── Internal job record ───────────────────────────────────────────────────────

class Job(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.pending
    prompt: str
    enhanced_prompt: Optional[str] = None
    progress: int = 0
    message: str = "Queued"
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Generation params (resolved from request + defaults)
    num_frames: int = 64
    num_inference_steps: int = 8
    guidance_scale: float = 1.0
    width: int = 512
    height: int = 512

    def to_response(self) -> JobResponse:
        return JobResponse(**self.model_dump())


# ── WebSocket messages ────────────────────────────────────────────────────────

class WSMessageType(str, Enum):
    progress = "progress"
    completed = "completed"
    error = "error"
    state = "state"


class WSMessage(BaseModel):
    type: WSMessageType
    job_id: str
    percent: Optional[int] = None
    message: Optional[str] = None
    video_url: Optional[str] = None
    enhanced_prompt: Optional[str] = None
    status: Optional[JobStatus] = None
    error: Optional[str] = None
