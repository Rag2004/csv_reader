"""Post-load entry/exit price slippage for CSV Reader analytics."""

from __future__ import annotations

import math

from app.schemas.trades import NormalizedTrade


def _can_apply_price_slip(t: NormalizedTrade) -> bool:
    if t.side not in (1, -1):
        return False
    if t.quantity is None or t.quantity == 0:
        return False
    if t.entry_price is None or t.exit_price is None:
        return False
    if not math.isfinite(t.entry_price) or not math.isfinite(t.exit_price):
        return False
    return True


def apply_slippage_pct(
    trades: list[NormalizedTrade],
    pct: float,
) -> list[NormalizedTrade]:
    """Apply adverse % slippage to entry/exit prices, then recompute PnL.

    Buy (side=1):  entry*(1+s), exit*(1-s)
    Sell (side=-1): entry*(1-s), exit*(1+s)
    slipped_pnl = side * (exit_slipped - entry_slipped) * quantity

    Skips rows missing usable entry_price, exit_price, side, or quantity
    (keeps current pnl). Stores extras["raw_pnl"] when not already set.
    No-op when pct == 0.
    """
    if pct == 0:
        return trades
    if pct < 0 or pct > 100:
        raise ValueError("slippage_pct must be between 0 and 100 inclusive")

    s = pct / 100.0
    out: list[NormalizedTrade] = []
    for t in trades:
        extras = dict(t.extras or {})
        if "raw_pnl" not in extras:
            extras["raw_pnl"] = t.pnl

        if not _can_apply_price_slip(t):
            out.append(t.model_copy(update={"extras": extras}))
            continue

        assert t.side is not None and t.quantity is not None
        assert t.entry_price is not None and t.exit_price is not None

        if t.side == 1:
            entry_slipped = t.entry_price * (1.0 + s)
            exit_slipped = t.exit_price * (1.0 - s)
        else:
            entry_slipped = t.entry_price * (1.0 - s)
            exit_slipped = t.exit_price * (1.0 + s)

        slipped_pnl = float(t.side) * (exit_slipped - entry_slipped) * float(t.quantity)
        extras["entry_price_slipped"] = entry_slipped
        extras["exit_price_slipped"] = exit_slipped
        out.append(t.model_copy(update={"pnl": slipped_pnl, "extras": extras}))
    return out
