from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # ── AnimateDiff / Stable Diffusion ────────────────────────────────────────
    motion_adapter_id: str = "guoyww/animatediff-motion-adapter-v1-5-2"
    base_model_id: str = "runwayml/stable-diffusion-v1-5"
    torch_dtype: str = "float16"   # used as string; converted in models.py
    device: str = "mps"            # "mps" | "cuda" | "cpu"

    # ── Generation defaults ───────────────────────────────────────────────────
    # num_frames=8 avoids the 16-frame × spatial-attention OOM on Apple Silicon.
    # SD 1.5 native resolution is 512×512; going lower hurts quality more than
    # reducing frames does.
    num_frames: int = 8
    width: int = 512
    height: int = 512
    num_inference_steps: int = 25
    guidance_scale: float = 7.5
    fps: int = 8

    # ── MLX LLM ───────────────────────────────────────────────────────────────
    llm_model_id: str = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
    llm_max_tokens: int = 200
    llm_temp: float = 0.7

    # ── Paths ─────────────────────────────────────────────────────────────────
    outputs_dir: Path = Path(__file__).parent.parent / "outputs"

    model_config = {"env_prefix": "TTV_", "env_file": ".env"}


settings = Settings()

# Ensure outputs directory exists
settings.outputs_dir.mkdir(parents=True, exist_ok=True)
