"""Post-load PnL slippage adjustments for CSV Reader analytics."""

from __future__ import annotations

from app.schemas.trades import NormalizedTrade


def apply_slippage_pct(
    trades: list[NormalizedTrade],
    pct: float,
) -> list[NormalizedTrade]:
    """Reduce each trade's PnL by abs(pnl) * (pct / 100).

    adjusted_pnl = pnl - abs(pnl) * (pct / 100)

    No-op when pct == 0. When pct > 0, original pnl is stored in extras["raw_pnl"].
    """
    if pct == 0:
        return trades
    if pct < 0 or pct > 100:
        raise ValueError("slippage_pct must be between 0 and 100 inclusive")

    factor = pct / 100.0
    out: list[NormalizedTrade] = []
    for t in trades:
        raw = t.pnl
        adjusted = raw - abs(raw) * factor
        extras = dict(t.extras or {})
        extras["raw_pnl"] = raw
        out.append(t.model_copy(update={"pnl": adjusted, "extras": extras}))
    return out
