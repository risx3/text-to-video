from pathlib import Path
from pydantic_settings import BaseSettings


def _default_device() -> str:
    """Auto-detect the best available compute device."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # ── AnimateDiff / Stable Diffusion ────────────────────────────────────────
    motion_adapter_id: str = "ByteDance/AnimateDiff-Lightning"
    base_model_id: str = "runwayml/stable-diffusion-v1-5"
    torch_dtype: str = "float16"   # used as string; converted in models.py
    # "auto" resolves to cuda > mps > cpu at model-load time.
    device: str = "auto"

    # ── Generation defaults ───────────────────────────────────────────────────
    # AnimateDiff-Lightning: 8 steps at guidance_scale=1.0 (distilled model).
    # FreeNoise sliding window enables longer generation beyond the 16-frame
    # training window. 64 frames @ 8 fps = 8 seconds of video.
    num_frames: int = 64
    width: int = 512
    height: int = 512
    num_inference_steps: int = 8
    guidance_scale: float = 1.0
    fps: int = 8
    # FreeNoise context window (must be ≤ num_frames, typically 16)
    free_noise_context_length: int = 16
    free_noise_context_stride: int = 4

    # ── MLX LLM (Apple Silicon only — optional on other platforms) ────────────
    # Set enable_llm=false on non-Apple or memory-constrained hosts to skip
    # prompt enhancement and use the raw prompt directly.
    enable_llm: bool = True
    llm_model_id: str = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
    llm_max_tokens: int = 200
    llm_temp: float = 0.7

    # ── Paths ─────────────────────────────────────────────────────────────────
    outputs_dir: Path = Path(__file__).parent.parent / "outputs"

    model_config = {"env_prefix": "TTV_", "env_file": ".env"}


settings = Settings()

# Resolve "auto" device once at startup
if settings.device == "auto":
    settings.device = _default_device()

# Ensure outputs directory exists
settings.outputs_dir.mkdir(parents=True, exist_ok=True)
