"""Download all required models from HuggingFace to a local directory."""

import os
from pathlib import Path
from huggingface_hub import snapshot_download

MODELS_DIR = Path(__file__).parent / "models"

MODELS = {
    "animatediff-lightning": "ByteDance/AnimateDiff-Lightning",
    "stable-diffusion-v1-5": "runwayml/stable-diffusion-v1-5",
    "qwen2.5-1.5b-instruct-4bit": "mlx-community/Qwen2.5-1.5B-Instruct-4bit",
}


def main():
    MODELS_DIR.mkdir(exist_ok=True)

    for folder, repo_id in MODELS.items():
        dest = MODELS_DIR / folder
        print(f"\n{'='*60}")
        print(f"Downloading {repo_id} → {dest}")
        print(f"{'='*60}")
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(dest),
        )
        print(f"Done: {repo_id}")

    print(f"\n{'='*60}")
    print("All models downloaded. Set these in your .env:")
    print(f"  TTV_MOTION_ADAPTER_ID={MODELS_DIR / 'animatediff-lightning'}")
    print(f"  TTV_BASE_MODEL_ID={MODELS_DIR / 'stable-diffusion-v1-5'}")
    print(f"  TTV_LLM_MODEL_ID={MODELS_DIR / 'qwen2.5-1.5b-instruct-4bit'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
