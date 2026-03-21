"""Serve generated video/GIF files."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.core.config import settings

router = APIRouter()

_ALLOWED_SUFFIXES = {".gif", ".mp4", ".webm"}
_MEDIA_TYPES = {
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
}


@router.get("/videos/{filename}")
async def get_video(filename: str):
    """Serve a generated GIF or MP4 by filename."""
    # Reject any path separators or traversal sequences before touching the FS
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = (settings.outputs_dir / filename).resolve()

    # Verify the resolved path is strictly inside the outputs directory
    # (guards against symlink traversal and encoded sequences)
    try:
        path.relative_to(settings.outputs_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    suffix = path.suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    return FileResponse(
        path=str(path),
        media_type=_MEDIA_TYPES[suffix],
        filename=filename,
    )
