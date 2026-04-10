from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

_UI_FILE = Path(__file__).resolve().parent / "webui" / "index.html"


@router.get("/ui", response_class=HTMLResponse)
def serve_ui() -> HTMLResponse:
    if not _UI_FILE.exists():
        raise HTTPException(status_code=404, detail="UI file not found.")
    return HTMLResponse(_UI_FILE.read_text(encoding="utf-8"))


@router.get("/api/v1/debug/file")
def debug_file(path: str = Query(..., min_length=1)) -> FileResponse:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path=file_path, filename=file_path.name)
