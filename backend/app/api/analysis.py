"""Cached analysis slice endpoints — no recomputation (cookie-scoped)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.cookies import read_session_id
from app.core import session as session_store
from app.schemas.analysis import EquityResponse, MonthlyResponse, OverviewResponse
from app.schemas.responses import TradesResponse
from app.schemas.trades import NormalizedTrade

router = APIRouter(tags=["analysis"])


def _require_bundle(request: Request):
    bundle = session_store.get_bundle(read_session_id(request))
    if bundle is None:
        raise HTTPException(status_code=404, detail="No CSV loaded. Upload a file first.")
    return bundle


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(request: Request):
    return _require_bundle(request).overview


@router.get("/equity", response_model=EquityResponse)
async def get_equity(request: Request):
    return _require_bundle(request).equity


@router.get("/monthly", response_model=MonthlyResponse)
async def get_monthly(request: Request):
    return _require_bundle(request).monthly


@router.get("/trades", response_model=TradesResponse)
async def get_trades(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=2000),
    side: int | None = Query(None, description="1 long, -1 short"),
    pnl_sign: str | None = Query(None, description="win | loss | all"),
    symbol: str | None = None,
    exit_type: str | None = None,
    start: date | None = None,
    end: date | None = None,
):
    bundle = _require_bundle(request)
    rows: list[NormalizedTrade] = list(bundle.trades)

    if side is not None:
        rows = [t for t in rows if t.side == side]
    if pnl_sign == "win":
        rows = [t for t in rows if t.pnl > 0]
    elif pnl_sign == "loss":
        rows = [t for t in rows if t.pnl <= 0]
    if symbol:
        sym = symbol.lower()
        rows = [t for t in rows if t.symbol and sym in t.symbol.lower()]
    if exit_type:
        et = exit_type.lower()
        rows = [t for t in rows if t.exit_type and et in t.exit_type.lower()]
    if start:
        rows = [t for t in rows if t.entry_time.date() >= start]
    if end:
        rows = [t for t in rows if t.entry_time.date() <= end]

    total = len(rows)
    page = rows[offset : offset + limit]
    return TradesResponse(trades=page, total=total, offset=offset, limit=limit)
