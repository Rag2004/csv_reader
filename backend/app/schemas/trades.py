from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NormalizedTrade(BaseModel):
    """Canonical trade row after smart CSV normalization."""

    entry_time: datetime
    exit_time: datetime | None = None
    pnl: float
    symbol: str | None = None
    side: int | None = None  # 1 long, -1 short, or None
    quantity: float | None = None
    entry_price: float | None = None
    exit_price: float | None = None
    exit_type: str | None = None
    strategy: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)
