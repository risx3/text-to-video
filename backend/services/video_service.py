"""AnimateDiff pipeline orchestration with WebSocket progress callbacks."""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Callable, Awaitable

import torch

from backend.core.config import settings
from backend.core.models import get_pipe
from backend.schemas.job import JobStatus
from backend.services import job_service
from backend.services.llm_service import enhance_prompt

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str], Awaitable[None]]


def _free_device_cache() -> None:
    """Release cached memory on the active compute device."""
    try:
        device = settings.device
        if device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif device == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
            torch.mps.empty_cache()
        # CPU has no explicit cache to free
    except Exception as exc:
        logger.debug("Device cache release skipped: %s", exc)


async def run_job(
    job_id: str,
    on_progress: ProgressCallback,
) -> None:
    """
    Full pipeline for a single job:
      1. Enhance prompt via LLM (optional)
      2. Run AnimateDiff
      3. Export MP4
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
        loop = asyncio.get_running_loop()

        def step_callback(pipe_inner, step: int, timestep, callback_kwargs):
            # Map inference steps → 12–90% range
            pct = 12 + int((step / total_steps) * 78)
            msg = f"Denoising step {step}/{total_steps}"
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

        # ── Step 5: Export MP4 ────────────────────────────────────────────────
        await on_progress(92, "Exporting MP4…")

        mp4_filename = f"{uuid.uuid4()}.mp4"
        mp4_path = settings.outputs_dir / mp4_filename

        def _export():
            import imageio
            import numpy as np
            writer = imageio.get_writer(
                str(mp4_path), fps=settings.fps, codec="libx264",
                quality=8, pixelformat="yuv420p",
            )
            for frame in frames:
                writer.append_data(np.array(frame))
            writer.close()

        await loop.run_in_executor(None, _export)

        video_url = f"/api/videos/{mp4_filename}"
        job_service.update_job(
            job_id,
            status=JobStatus.completed,
            video_url=video_url,
            progress=100,
            message="Done!",
        )
        await on_progress(100, "Done!")
        logger.info("Job %s completed → %s", job_id, mp4_path)

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
        _free_device_cache()
