"""Case-insensitive column aliases for smart CSV mapping."""

from __future__ import annotations

import re


def normalize_header(name: str) -> str:
    """Collapse header to a comparable key: lower, strip, unify separators."""
    s = str(name).replace("\ufeff", "").strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[\s\-./]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


# logical_field -> ordered list of normalized alias keys
FIELD_ALIASES: dict[str, list[str]] = {
    "pnl": [
        "pnl",
        "p_and_l",
        "pandl",
        "profit",
        "net_pnl",
        "net_p_and_l",
        "netpnl",
        "realized_pnl",
        "realizedpnl",
        "pl",
        "net_profit",
        "trade_pnl",
    ],
    "entry_time": [
        "key",
        "entry_time",
        "entrytime",
        "entry_date",
        "entrydate",
        "datetime",
        "date",
        "trade_date",
        "tradedate",
        "open_time",
        "opentime",
        "entry",
    ],
    "exit_time": [
        "exit_time",
        "exittime",
        "exit_date",
        "exitdate",
        "close_time",
        "closetime",
        "exit",
    ],
    "side": [
        "position_status",
        "positionstatus",
        "side",
        "direction",
        "pos",
        "position",
    ],
    "symbol": [
        "symbol",
        "ticker",
        "instrument",
        "underlying",
        "scrip",
    ],
    "quantity": [
        "quantity",
        "qty",
        "lots",
        "lot",
        "size",
        "contracts",
    ],
    "entry_price": [
        "entry_price",
        "entryprice",
        "entry_px",
        "entrypx",
        "buy_price",
        "open_price",
        "openprice",
    ],
    "exit_price": [
        "exit_price",
        "exitprice",
        "exit_px",
        "exitpx",
        "sell_price",
        "close_price",
        "closeprice",
    ],
    "exit_type": [
        "exit_type",
        "exittype",
        "exit_reason",
        "exitreason",
        "reason",
    ],
    "strategy": [
        "strategy",
        "strategy_name",
        "strat",
        "algo",
    ],
}

REQUIRED_FIELDS = ("pnl",)
TIMESTAMP_FIELDS = ("entry_time", "exit_time")
