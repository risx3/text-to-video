"""AnimateDiff pipeline orchestration with WebSocket progress callbacks."""
from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Callable, Awaitable

import torch

from backend.core.config import settings
from backend.core.models import get_pipe
from backend.schemas.job import JobStatus
from backend.services import job_service
from backend.services.llm_service import enhance_prompt

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str], Awaitable[None]]


async def run_job(
    job_id: str,
    on_progress: ProgressCallback,
) -> None:
    """
    Full pipeline for a single job:
      1. Enhance prompt via LLM
      2. Run AnimateDiff
      3. Export GIF
      4. Update job store + call progress callback
    """
    job = job_service.get_job(job_id)
    if job is None:
        logger.error("Job %s not found", job_id)
        return

    try:
        # ── Step 1: Enhance prompt ────────────────────────────────────────────
        job_service.set_status(job_id, JobStatus.enhancing, "Enhancing prompt…")
        await on_progress(5, "Enhancing prompt with LLM…")

        enhanced = await enhance_prompt(job.prompt)
        job_service.update_job(job_id, enhanced_prompt=enhanced)
        await on_progress(10, f"Prompt enhanced: {enhanced[:80]}…")

        # ── Step 2: Load pipeline ─────────────────────────────────────────────
        job_service.set_status(job_id, JobStatus.generating, "Loading model…")
        await on_progress(12, "Loading AnimateDiff model…")
        pipe = await get_pipe()

        # ── Step 3: Build diffusers callback ──────────────────────────────────
        total_steps = job.num_inference_steps
        loop = asyncio.get_event_loop()

        def step_callback(pipe_inner, step: int, timestep, callback_kwargs):
            # Map inference steps → 12–90% range
            pct = 12 + int((step / total_steps) * 78)
            msg = f"Generating frame {step}/{total_steps}"
            # Schedule coroutine on event loop from sync context
            asyncio.run_coroutine_threadsafe(
                on_progress(pct, msg), loop
            )
            return callback_kwargs

        # ── Step 4: Inference ─────────────────────────────────────────────────
        def _run_inference():
            with torch.inference_mode():
                output = pipe(
                    prompt=enhanced,
                    num_frames=job.num_frames,
                    width=job.width,
                    height=job.height,
                    num_inference_steps=total_steps,
                    guidance_scale=job.guidance_scale,
                    callback_on_step_end=step_callback,
                )
            return output.frames[0]

        frames = await loop.run_in_executor(None, _run_inference)

        # ── Step 5: Export GIF ────────────────────────────────────────────────
        await on_progress(92, "Exporting GIF…")

        gif_filename = f"{uuid.uuid4()}.gif"
        gif_path = settings.outputs_dir / gif_filename

        def _export():
            from diffusers.utils import export_to_gif
            export_to_gif(frames, str(gif_path), fps=settings.fps)

        await loop.run_in_executor(None, _export)

        video_url = f"/api/videos/{gif_filename}"
        job_service.update_job(
            job_id,
            status=JobStatus.completed,
            video_url=video_url,
            progress=100,
            message="Done!",
        )
        await on_progress(100, "Done!")
        logger.info("Job %s completed → %s", job_id, gif_path)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        err_msg = str(exc)
        job_service.update_job(
            job_id,
            status=JobStatus.failed,
            error=err_msg,
            message=f"Error: {err_msg}",
        )
        await on_progress(-1, f"Error: {err_msg}")
        raise

    finally:
        # Free MPS memory after each job
        try:
            torch.mps.empty_cache()
        except Exception:
            pass
