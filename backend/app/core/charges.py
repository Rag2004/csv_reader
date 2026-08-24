"""Post-load flat per-trade charge adjustments for CSV Reader analytics."""

from __future__ import annotations

from app.schemas.trades import NormalizedTrade


def apply_charge_per_trade(
    trades: list[NormalizedTrade],
    amount: float,
) -> list[NormalizedTrade]:
    """Subtract a flat ₹ amount from each trade's PnL.

    net_pnl = pnl - amount

    No-op when amount == 0. When amount > 0, stores extras["charges"] and
    extras["raw_pnl"] (CSV original) if not already present.
    """
    if amount == 0:
        return trades
    if amount < 0:
        raise ValueError("charge_per_trade must be >= 0")

    out: list[NormalizedTrade] = []
    for t in trades:
        extras = dict(t.extras or {})
        if "raw_pnl" not in extras:
            extras["raw_pnl"] = t.pnl
        extras["charges"] = float(amount)
        adjusted = t.pnl - float(amount)
        out.append(t.model_copy(update={"pnl": adjusted, "extras": extras}))
    return out
