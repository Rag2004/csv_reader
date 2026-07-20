"""FastAPI entrypoint for the independent CSV Reader module."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import analysis, meta, upload

app = FastAPI(
    title="CSV Reader — Trade Analytics Workstation",
    version="1.0.0",
    description="Independent full-stack trade CSV analytics (upload once, cache metrics).",
)

_cors_origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
_extra = os.environ.get("CSV_READER_CORS_ORIGINS", "")
if _extra.strip():
    _cors_origins.extend(o.strip() for o in _extra.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "csv_reader"}


# Serve built frontend when present (Docker / production).
_static_dir = Path(
    os.environ.get("CSV_READER_STATIC", str(Path(__file__).resolve().parents[2] / "static"))
)
_index = _static_dir / "index.html"

if _static_dir.is_dir() and _index.is_file():
    assets = _static_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path in {"api", "health", "docs", "openapi.json", "redoc"}:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (_static_dir / full_path).resolve()
        try:
            candidate.relative_to(_static_dir.resolve())
        except ValueError:
            return FileResponse(_index)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_index)
