from __future__ import annotations

from pydantic import BaseModel, Field

from .analysis import OverviewResponse
from .meta import SessionMeta
from .trades import NormalizedTrade


class ErrorResponse(BaseModel):
    detail: str
    headers_seen: list[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    meta: SessionMeta
    overview: OverviewResponse


class TradesResponse(BaseModel):
    trades: list[NormalizedTrade]
    total: int
    offset: int = 0
    limit: int = 100
