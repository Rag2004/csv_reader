from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


def display_filename(filenames: list[str]) -> str:
    """Short label for sidebar / meta: one name, 'a + b', or 'a + N more'."""
    if not filenames:
        return ""
    if len(filenames) == 1:
        return filenames[0]
    if len(filenames) == 2:
        return f"{filenames[0]} + {filenames[1]}"
    return f"{filenames[0]} + {len(filenames) - 1} more"


class SessionMeta(BaseModel):
    """Public file metadata — no session id exposed to clients."""

    filename: str
    filenames: list[str] = Field(default_factory=list)
    row_count: int
    start_date: date | None = None
    end_date: date | None = None
    original_headers: list[str] = Field(default_factory=list)
    column_map: dict[str, str] = Field(default_factory=dict)
    loaded_at: datetime
    slippage_pct: float = 0.0
    brokerage_per_order: float = 0.0
