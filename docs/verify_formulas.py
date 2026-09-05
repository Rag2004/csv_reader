"""
Independently recompute CSV-reader metrics and compare to compute_analysis().

Usage (from csv_reader/):
    python docs/verify_formulas.py
    python docs/verify_formulas.py path/to/trades.csv

Exit code 0 = all checks passed.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.loader import load_csv_path  # noqa: E402
from app.core.metrics import compute_analysis  # noqa: E402


def independent_overview(df: pd.DataFrame) -> dict:
    """Mirror metrics.py formulas in one place for verification."""
    df = df.copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
    df = df.dropna(subset=["entry_time"])
    if getattr(df["entry_time"].dt, "tz", None) is not None:
        df["entry_time"] = df["entry_time"].dt.tz_localize(None)
    df["trade_date"] = df["entry_time"].dt.date

    total_trades = len(df)
    total_pnl = float(df["pnl"].sum())
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]
    win_trades = len(wins)
    loss_trades = len(losses)
    avg_win = round(float(wins["pnl"].mean()), 2) if win_trades else 0.0
    avg_loss = round(float(losses["pnl"].mean()), 2) if loss_trades else 0.0

    daily = df.groupby("trade_date")["pnl"].sum().sort_index()
    total_days = len(daily)
    profit_days = int((daily > 0).sum())
    loss_days = int((daily < 0).sum())
    profit_days_pct = round(profit_days / total_days * 100, 2) if total_days else 0.0
    win_rate = profit_days_pct
    avg_profit_on_profit_days = (
        round(float(daily[daily > 0].mean()), 2) if profit_days else 0.0
    )
    avg_loss_on_loss_days = (
        round(float(daily[daily < 0].mean()), 2) if loss_days else 0.0
    )

    equity = daily.cumsum()
    drawdown = equity - equity.cummax()
    max_drawdown = round(float(drawdown.min()), 2) if len(drawdown) else 0.0

    dd_vals = sorted(float(x) for x in drawdown.values if x < 0)
    top5 = dd_vals[:5] if dd_vals else []
    top5_dd_avg = round(float(np.mean(top5)), 2) if top5 else 0.0
    loss_day_vals = sorted(float(x) for x in daily.values if x < 0)
    top5_ld = loss_day_vals[:5]
    top5_ld_avg = round(float(np.mean(top5_ld)), 2) if top5_ld else 0.0

    calmar = round(abs(total_pnl / max_drawdown), 2) if max_drawdown != 0 else 0.0
    recovery_factor = (
        round(abs(total_pnl / max_drawdown), 3) if max_drawdown != 0 else 0.0
    )

    df["month"] = df["entry_time"].dt.to_period("M")
    monthly_pnl = df.groupby("month")["pnl"].sum()
    total_months = len(monthly_pnl)
    avg_monthly = round(float(monthly_pnl.mean()), 2) if total_months else 0.0
    median_monthly = round(float(monthly_pnl.median()), 2) if total_months else 0.0

    neg_monthly = monthly_pnl[monthly_pnl < 0]
    downside_std = float(neg_monthly.std(ddof=0)) if len(neg_monthly) > 0 else 0.0
    sortino = round(avg_monthly / downside_std, 3) if downside_std != 0 else 0.0

    week = df["entry_time"].dt.isocalendar().week.astype(int)
    weekly_pnl = df.assign(week=week).groupby("week")["pnl"].sum()
    avg_weekly = round(float(weekly_pnl.mean()), 2) if len(weekly_pnl) else 0.0

    avg_pnl_per_trade = round(total_pnl / total_trades, 2) if total_trades else 0.0
    risk_reward = round(abs(avg_win / avg_loss), 3) if avg_loss != 0 else 0.0
    if isinstance(risk_reward, float) and not math.isfinite(risk_reward):
        risk_reward = 0.0

    win_pct_frac = win_trades / total_trades if total_trades else 0.0
    loss_pct_frac = loss_trades / total_trades if total_trades else 0.0
    expectancy = round(win_pct_frac * avg_win + loss_pct_frac * avg_loss, 3)

    gross_wins = float(wins["pnl"].sum()) if win_trades else 0.0
    gross_losses = abs(float(losses["pnl"].sum())) if loss_trades else 0.0
    profit_factor = round(gross_wins / gross_losses, 3) if gross_losses > 0 else 0.0

    mean_daily = round(float(daily.mean()), 4) if total_days else 0.0
    std_dev = round(float(daily.std(ddof=0)), 4) if total_days else 0.0
    mean_std = round(mean_daily / std_dev, 4) if std_dev != 0 else 0.0
    sharpe = (
        round(mean_daily / std_dev * math.sqrt(252), 3) if std_dev != 0 else 0.0
    )
    trade_std = float(df["pnl"].std(ddof=0))
    sqn = (
        round(math.sqrt(total_trades) * (avg_pnl_per_trade / trade_std), 2)
        if total_trades > 1 and trade_std != 0
        else 0.0
    )

    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": win_rate,
        "calmar": calmar,
        "max_drawdown": max_drawdown,
        "total_trades": total_trades,
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "profit_days": profit_days,
        "loss_days": loss_days,
        "total_days": total_days,
        "total_months": total_months,
        "avg_monthly": avg_monthly,
        "median_monthly": median_monthly,
        "avg_weekly": avg_weekly,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_pnl_per_trade": avg_pnl_per_trade,
        "risk_reward": risk_reward,
        "expectancy": expectancy,
        "avg_profit_on_profit_days": avg_profit_on_profit_days,
        "avg_loss_on_loss_days": avg_loss_on_loss_days,
        "profit_days_pct": profit_days_pct,
        "top5_dd_avg": top5_dd_avg,
        "top5_ld_avg": top5_ld_avg,
        "profit_factor": profit_factor,
        "recovery_factor": recovery_factor,
        "sortino": sortino,
        "sharpe": sharpe,
        "sqn": sqn,
        "mean_daily": mean_daily,
        "std_dev": std_dev,
        "mean_std": mean_std,
    }


def _almost(a, b, tol=1e-9) -> bool:
    if isinstance(a, (int, np.integer)) and isinstance(b, (int, np.integer)):
        return int(a) == int(b)
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def main() -> int:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "samples" / "sample_trades.csv"
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 1

    trades, column_map, original_headers, filename = load_csv_path(str(csv_path))
    bundle = compute_analysis(
        trades,
        filename=filename or csv_path.name,
        original_headers=original_headers,
        column_map=column_map,
    )
    engine = bundle.overview.model_dump()

    df = pd.DataFrame(
        [{"entry_time": t.entry_time, "pnl": t.pnl} for t in trades]
    )
    indep = independent_overview(df)

    keys = sorted(indep.keys())
    failed = []
    print(f"Verifying {len(keys)} metrics against {csv_path.name} ({len(trades)} trades)\n")
    print(f"{'Metric':<28} {'Engine':>14} {'Independent':>14}  Status")
    print("-" * 70)
    for k in keys:
        e, i = engine.get(k), indep[k]
        ok = _almost(e, i)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(k)
        print(f"{k:<28} {e!s:>14} {i!s:>14}  {status}")

    print("-" * 70)
    # Sanity: Calmar vs Recovery Factor differ only by rounding
    if engine["max_drawdown"] != 0:
        c = abs(engine["total_pnl"] / engine["max_drawdown"])
        print(f"\nNote: Calmar (2dp)={engine['calmar']}, Recovery (3dp)={engine['recovery_factor']}")
        print(f"      Same raw ratio ~ {c:.6f} (confirm with team if both labels should differ)")

    if failed:
        print(f"\nFAILED: {len(failed)} metric(s): {', '.join(failed)}")
        return 1
    print(f"\nALL {len(keys)} METRICS MATCH compute_analysis().")
    print("Open docs/CSV_Reader_Formulas.xlsx for the human-readable formula list.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
