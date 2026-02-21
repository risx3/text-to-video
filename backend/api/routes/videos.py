"""Serve generated video/GIF files."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.core.config import settings

router = APIRouter()


@router.get("/videos/{filename}")
async def get_video(filename: str):
    """Serve a generated GIF or MP4 by filename."""
    # Prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = settings.outputs_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    suffix = path.suffix.lower()
    media_type_map = {
        ".gif": "image/gif",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }
    media_type = media_type_map.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=filename,
    )
