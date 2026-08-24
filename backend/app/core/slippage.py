"""Post-load PnL slippage adjustments for CSV Reader analytics."""

from __future__ import annotations

from app.schemas.trades import NormalizedTrade


def apply_slippage_pct(
    trades: list[NormalizedTrade],
    pct: float,
) -> list[NormalizedTrade]:
    """Reduce each trade's PnL by abs(original_pnl) * (pct / 100).

    adjusted_pnl = pnl - abs(raw_pnl) * (pct / 100)

    Uses extras["raw_pnl"] when present (CSV original); otherwise current pnl.
    No-op when pct == 0. Does not overwrite extras["raw_pnl"] if already set.
    """
    if pct == 0:
        return trades
    if pct < 0 or pct > 100:
        raise ValueError("slippage_pct must be between 0 and 100 inclusive")

    factor = pct / 100.0
    out: list[NormalizedTrade] = []
    for t in trades:
        extras = dict(t.extras or {})
        if "raw_pnl" in extras:
            raw = float(extras["raw_pnl"])
        else:
            raw = t.pnl
            extras["raw_pnl"] = raw
        adjusted = t.pnl - abs(raw) * factor
        out.append(t.model_copy(update={"pnl": adjusted, "extras": extras}))
    return out
