"""Post-load F&O trading charge adjustments for CSV Reader analytics."""

from __future__ import annotations

import math

from app.schemas.trades import NormalizedTrade


SELL_RATE = 0.00192043
BUY_RATE = 0.00045043
N_ORDERS = 2
GST_MULTIPLIER = 1.18


def _can_apply_charges(t: NormalizedTrade) -> bool:
    if t.side not in (1, -1):
        return False
    if t.quantity is None or not math.isfinite(t.quantity) or t.quantity <= 0:
        return False
    if t.entry_price is None or t.exit_price is None:
        return False
    return math.isfinite(t.entry_price) and math.isfinite(t.exit_price)


def apply_charges(
    trades: list[NormalizedTrade],
    brokerage_per_order: float,
) -> list[NormalizedTrade]:
    """Calculate side-aware F&O charges and subtract them from each trade.

    charges = 1.18 * 2 * brokerage_per_order
              + quantity * (SELL_RATE * sell_price + BUY_RATE * buy_price)

    Slipped prices are used when available. Rows without usable prices, side,
    or quantity are left unchanged and record zero charges.
    """
    if not math.isfinite(brokerage_per_order) or brokerage_per_order < 0:
        raise ValueError("brokerage_per_order must be a finite number >= 0")

    brokerage = GST_MULTIPLIER * N_ORDERS * float(brokerage_per_order)
    out: list[NormalizedTrade] = []
    for t in trades:
        extras = dict(t.extras or {})
        if "raw_pnl" not in extras:
            extras["raw_pnl"] = t.pnl

        if not _can_apply_charges(t):
            extras["charges"] = 0.0
            out.append(t.model_copy(update={"extras": extras}))
            continue

        assert t.entry_price is not None and t.exit_price is not None
        assert t.quantity is not None and t.side is not None

        entry_price = float(extras.get("entry_price_slipped", t.entry_price))
        exit_price = float(extras.get("exit_price_slipped", t.exit_price))
        if not math.isfinite(entry_price) or not math.isfinite(exit_price):
            extras["charges"] = 0.0
            out.append(t.model_copy(update={"extras": extras}))
            continue

        if t.side == -1:
            sell_price, buy_price = entry_price, exit_price
        else:
            buy_price, sell_price = entry_price, exit_price

        charges = brokerage + float(t.quantity) * (
            SELL_RATE * sell_price + BUY_RATE * buy_price
        )
        extras["charges"] = charges
        adjusted = t.pnl - charges
        out.append(t.model_copy(update={"pnl": adjusted, "extras": extras}))
    return out
