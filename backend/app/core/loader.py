"""Smart case-insensitive CSV loader → NormalizedTrade list."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import pandas as pd

from app.core.aliases import (
    FIELD_ALIASES,
    REQUIRED_FIELDS,
    TIMESTAMP_FIELDS,
    normalize_header,
)
from app.schemas.trades import NormalizedTrade


class CSVLoadError(Exception):
    def __init__(self, message: str, headers_seen: list[str] | None = None):
        super().__init__(message)
        self.message = message
        self.headers_seen = headers_seen or []


def _map_columns(headers: list[str]) -> dict[str, str]:
    """Map logical field → original header name."""
    norm_to_original: dict[str, str] = {}
    for h in headers:
        key = normalize_header(h)
        if key and key not in norm_to_original:
            norm_to_original[key] = h

    column_map: dict[str, str] = {}
    used_originals: set[str] = set()

    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in norm_to_original:
                original = norm_to_original[alias]
                if original in used_originals:
                    continue
                column_map[field] = original
                used_originals.add(original)
                break

    return column_map


def _parse_number(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "null", "-"}:
        return None
    s = s.replace("₹", "").replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.to_pydatetime()
    s = str(value).strip()
    # Prefer day-first when ambiguous (common in Indian trade exports)
    ts = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if pd.isna(ts):
        ts = pd.to_datetime(s, errors="coerce", dayfirst=False)
    if pd.isna(ts):
        return None
    return ts.to_pydatetime()


def _parse_side(value: Any) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        v = int(value)
        if v in (1, -1, 0):
            return v if v != 0 else None
        return v
    s = str(value).strip().lower()
    if s in {"1", "long", "buy", "b", "l"}:
        return 1
    if s in {"-1", "short", "sell", "s"}:
        return -1
    try:
        return int(float(s))
    except ValueError:
        return None


def load_csv_bytes(data: bytes, filename: str = "upload.csv") -> tuple[list[NormalizedTrade], dict[str, str], list[str]]:
    """Parse CSV bytes into normalized trades.

    Returns:
        (trades, column_map, original_headers)
    """
    try:
        df = pd.read_csv(io.BytesIO(data))
    except Exception as exc:
        raise CSVLoadError(f"Failed to parse CSV: {exc}") from exc

    if df.empty:
        raise CSVLoadError("CSV is empty (no rows).")

    original_headers = [str(c) for c in df.columns.tolist()]
    column_map = _map_columns(original_headers)

    for req in REQUIRED_FIELDS:
        if req not in column_map:
            raise CSVLoadError(
                f"Could not find a P&L column. Looked for aliases of '{req}'. "
                f"Headers seen: {original_headers}",
                headers_seen=original_headers,
            )

    if not any(f in column_map for f in TIMESTAMP_FIELDS):
        raise CSVLoadError(
            "Could not find an entry or exit time column. "
            f"Headers seen: {original_headers}",
            headers_seen=original_headers,
        )

    mapped_originals = set(column_map.values())
    trades: list[NormalizedTrade] = []

    for _, row in df.iterrows():
        pnl = _parse_number(row.get(column_map["pnl"]))
        if pnl is None:
            continue

        entry_col = column_map.get("entry_time")
        exit_col = column_map.get("exit_time")
        entry_time = _parse_datetime(row.get(entry_col)) if entry_col else None
        exit_time = _parse_datetime(row.get(exit_col)) if exit_col else None

        if entry_time is None and exit_time is None:
            continue
        if entry_time is None:
            entry_time = exit_time

        extras: dict[str, Any] = {}
        for h in original_headers:
            if h not in mapped_originals:
                val = row.get(h)
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    extras[h] = val if not hasattr(val, "item") else val.item()

        def _opt_str(field: str) -> str | None:
            col = column_map.get(field)
            if not col:
                return None
            v = row.get(col)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            s = str(v).strip()
            return s or None

        qty = None
        if "quantity" in column_map:
            qty = _parse_number(row.get(column_map["quantity"]))

        side = None
        if "side" in column_map:
            side = _parse_side(row.get(column_map["side"]))

        trades.append(
            NormalizedTrade(
                entry_time=entry_time,
                exit_time=exit_time,
                pnl=float(pnl),
                symbol=_opt_str("symbol"),
                side=side,
                quantity=qty,
                exit_type=_opt_str("exit_type"),
                strategy=_opt_str("strategy"),
                extras=extras,
            )
        )

    if not trades:
        raise CSVLoadError(
            "No valid trade rows after parsing (need P&L + timestamp).",
            headers_seen=original_headers,
        )

    return trades, column_map, original_headers


def load_csv_path(path: str) -> tuple[list[NormalizedTrade], dict[str, str], list[str], str]:
    """Load from filesystem path. Returns trades, column_map, headers, filename."""
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        raise CSVLoadError(f"File not found: {path}")
    if p.suffix.lower() != ".csv":
        raise CSVLoadError("Only .csv files are supported.")
    data = p.read_bytes()
    trades, column_map, headers = load_csv_bytes(data, filename=p.name)
    return trades, column_map, headers, p.name
