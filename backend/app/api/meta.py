"""GET /api/meta — lightweight file metadata (cookie-scoped)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.cookies import read_session_id
from app.core import session as session_store
from app.schemas.meta import SessionMeta

router = APIRouter(tags=["meta"])


@router.get("/meta", response_model=SessionMeta)
async def get_meta(request: Request):
    bundle = session_store.get_bundle(read_session_id(request))
    if bundle is None:
        raise HTTPException(status_code=404, detail="No CSV loaded. Upload a file first.")
    return bundle.meta
