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

def _resolve_dtype() -> torch.dtype:
    """Select appropriate dtype for the current device."""
    device = settings.device
    # CPU does not support float16 reliably on all ops; use float32 there.
    if device == "cpu":
        return torch.float32
    return torch.float16 if settings.torch_dtype == "float16" else torch.float32


def _load_pipe_sync() -> Any:
    """Blocking loader — run in executor to avoid blocking event loop."""
    from diffusers import AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
    from diffusers.utils import USE_PEFT_BACKEND  # noqa: F401 (ensures compat)
    from huggingface_hub import hf_hub_download

    dtype = _resolve_dtype()
    device = settings.device

    logger.info("Loading MotionAdapter: %s", settings.motion_adapter_id)

    # AnimateDiff-Lightning ships as bare safetensors files (no config.json),
    # so MotionAdapter.from_pretrained won't work. Load weights manually.
    if "AnimateDiff-Lightning" in settings.motion_adapter_id:
        from safetensors.torch import load_file
        steps = settings.num_inference_steps
        ckpt = f"animatediff_lightning_{steps}step_diffusers.safetensors"
        logger.info("Downloading Lightning checkpoint: %s", ckpt)
        adapter = MotionAdapter()
        adapter.load_state_dict(
            load_file(hf_hub_download(settings.motion_adapter_id, ckpt), device="cpu")
        )
        adapter = adapter.to(dtype=dtype)
    else:
        adapter = MotionAdapter.from_pretrained(
            settings.motion_adapter_id, torch_dtype=dtype
        )

    logger.info("Loading AnimateDiffPipeline: %s", settings.base_model_id)
    pipe = AnimateDiffPipeline.from_pretrained(
        settings.base_model_id,
        motion_adapter=adapter,
        torch_dtype=dtype,
    )
    # Lightning requires clean scheduler params — do NOT inherit from the SD1.5
    # PNDM config (which uses beta_schedule="scaled_linear" and PNDM-specific
    # keys). Use an explicit init with exactly the values Lightning was trained on.
    if "AnimateDiff-Lightning" in settings.motion_adapter_id:
        pipe.scheduler = EulerDiscreteScheduler(
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="linear",
            timestep_spacing="trailing",
        )
    else:
        pipe.scheduler = EulerDiscreteScheduler.from_config(
            pipe.scheduler.config, beta_schedule="linear"
        )

    logger.info("Moving pipeline to device: %s", device)
    pipe = pipe.to(device)

    # ── Memory optimisations ──────────────────────────────────────────────────
    # 1. Slice spatial self-attention to avoid one giant Q·Kᵀ matrix.
    pipe.enable_attention_slicing(1)

    # 2. Slice the VAE decode step — prevents a second large allocation.
    pipe.enable_vae_slicing()

    # 3. Chunk the UNet feed-forward pass along the batch (frame) dimension so
    #    only one frame at a time flows through the heavy linear projections.
    #    Especially important for MPS and low-VRAM CUDA GPUs.
    try:
        pipe.unet.enable_forward_chunking(chunk_size=1, dim=1)
        logger.info("UNet forward chunking enabled (chunk_size=1, dim=1).")
    except Exception as exc:
        logger.warning("Could not enable UNet forward chunking: %s", exc)

    # 4. Enable CPU offload for CUDA devices if available (reduces VRAM usage).
    if device == "cuda":
        try:
            pipe.enable_model_cpu_offload()
            logger.info("CUDA model CPU offload enabled.")
        except Exception as exc:
            logger.warning("Could not enable CPU offload: %s", exc)

    logger.info("AnimateDiff pipeline ready on %s.", device)
    return pipe


async def get_pipe() -> Any:
    global _pipe
    if _pipe is None:
        async with _pipe_lock:
            if _pipe is None:
                loop = asyncio.get_running_loop()
                _pipe = await loop.run_in_executor(None, _load_pipe_sync)
    return _pipe


# ── MLX LLM (Apple Silicon only) ─────────────────────────────────────────────

def _load_llm_sync() -> tuple[Any, Any]:
    """Blocking loader — run in executor. Returns (None, None) if mlx unavailable."""
    try:
        from mlx_lm import load
    except ImportError:
        logger.warning("mlx-lm not installed — prompt enhancement disabled.")
        return None, None

    logger.info("Loading MLX LLM: %s", settings.llm_model_id)
    model, tokenizer = load(settings.llm_model_id)
    logger.info("MLX LLM ready.")
    return model, tokenizer


async def get_llm() -> tuple[Any, Any]:
    global _llm_model, _llm_tokenizer
    if _llm_model is None:
        async with _llm_lock:
            if _llm_model is None:
                loop = asyncio.get_running_loop()
                _llm_model, _llm_tokenizer = await loop.run_in_executor(
                    None, _load_llm_sync
                )
    return _llm_model, _llm_tokenizer
