from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class SessionMeta(BaseModel):
    """Public file metadata — no session id exposed to clients."""

    filename: str
    row_count: int
    start_date: date | None = None
    end_date: date | None = None
    original_headers: list[str] = Field(default_factory=list)
    column_map: dict[str, str] = Field(default_factory=dict)
    loaded_at: datetime
