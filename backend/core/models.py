"""Lazy singleton loaders for AnimateDiff pipeline and MLX LLM."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import torch

from backend.core.config import settings

logger = logging.getLogger(__name__)

# ── Internal state ────────────────────────────────────────────────────────────
_pipe: Any = None
_pipe_lock = asyncio.Lock()

_llm_model: Any = None
_llm_tokenizer: Any = None
_llm_lock = asyncio.Lock()


# ── AnimateDiff ───────────────────────────────────────────────────────────────

def _load_pipe_sync() -> Any:
    """Blocking loader — run in executor to avoid blocking event loop."""
    from diffusers import AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
    from diffusers.utils import USE_PEFT_BACKEND  # noqa: F401 (ensures compat)
    from huggingface_hub import snapshot_download  # noqa: F401

    dtype = torch.float16 if settings.torch_dtype == "float16" else torch.float32

    logger.info("Loading MotionAdapter: %s", settings.motion_adapter_id)
    adapter = MotionAdapter.from_pretrained(
        settings.motion_adapter_id, torch_dtype=dtype
    )

    logger.info("Loading AnimateDiffPipeline: %s", settings.base_model_id)
    pipe = AnimateDiffPipeline.from_pretrained(
        settings.base_model_id,
        motion_adapter=adapter,
        torch_dtype=dtype,
    )
    pipe.scheduler = EulerDiscreteScheduler.from_config(
        pipe.scheduler.config,
        beta_schedule="linear",
        timestep_spacing="trailing",
    )

    device = settings.device
    logger.info("Moving pipeline to device: %s", device)
    pipe = pipe.to(device)

    # ── Memory optimisations (critical for MPS / Apple Silicon) ───────────────
    # 1. Slice spatial self-attention to avoid one giant Q·Kᵀ matrix.
    pipe.enable_attention_slicing(1)

    # 2. Slice the VAE decode step — prevents a second large allocation.
    pipe.enable_vae_slicing()

    # 3. Chunk the UNet feed-forward pass along the batch (frame) dimension so
    #    only one frame at a time flows through the heavy linear projections.
    #    This is the fix for the 16 GiB single-MTLBuffer OOM with 16 frames.
    try:
        pipe.unet.enable_forward_chunking(chunk_size=1, dim=1)
        logger.info("UNet forward chunking enabled (chunk_size=1, dim=1).")
    except Exception as exc:
        logger.warning("Could not enable UNet forward chunking: %s", exc)

    logger.info("AnimateDiff pipeline ready.")
    return pipe


async def get_pipe() -> Any:
    global _pipe
    if _pipe is None:
        async with _pipe_lock:
            if _pipe is None:
                loop = asyncio.get_event_loop()
                _pipe = await loop.run_in_executor(None, _load_pipe_sync)
    return _pipe


# ── MLX LLM ───────────────────────────────────────────────────────────────────

def _load_llm_sync() -> tuple[Any, Any]:
    """Blocking loader — run in executor."""
    from mlx_lm import load

    logger.info("Loading MLX LLM: %s", settings.llm_model_id)
    model, tokenizer = load(settings.llm_model_id)
    logger.info("MLX LLM ready.")
    return model, tokenizer


async def get_llm() -> tuple[Any, Any]:
    global _llm_model, _llm_tokenizer
    if _llm_model is None:
        async with _llm_lock:
            if _llm_model is None:
                loop = asyncio.get_event_loop()
                _llm_model, _llm_tokenizer = await loop.run_in_executor(
                    None, _load_llm_sync
                )
    return _llm_model, _llm_tokenizer
