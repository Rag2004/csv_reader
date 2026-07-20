"""Self-contained metrics engine — compute once into AnalysisBundle."""

from __future__ import annotations

import math
from datetime import date, datetime

import numpy as np
import pandas as pd

from app.schemas.analysis import (
    AnalysisBundle,
    EquityPoint,
    EquityResponse,
    MonthCell,
    MonthlyResponse,
    MonthlyYearRow,
    OverviewResponse,
)
from app.schemas.meta import SessionMeta
from app.schemas.trades import NormalizedTrade


def _empty_overview() -> OverviewResponse:
    return OverviewResponse(
        total_pnl=0.0,
        win_rate=0.0,
        calmar=0.0,
        max_drawdown=0.0,
        total_trades=0,
        win_trades=0,
        loss_trades=0,
        profit_days=0,
        loss_days=0,
        total_days=0,
        total_months=0,
    )


def compute_analysis(
    trades: list[NormalizedTrade],
    *,
    filename: str,
    original_headers: list[str],
    column_map: dict[str, str],
    loaded_at: datetime | None = None,
) -> AnalysisBundle:
    """Compute full analysis bundle once after upload."""
    loaded_at = loaded_at or datetime.utcnow()

    if not trades:
        meta = SessionMeta(
            filename=filename,
            row_count=0,
            original_headers=original_headers,
            column_map=column_map,
            loaded_at=loaded_at,
        )
        return AnalysisBundle(
            meta=meta,
            trades=[],
            overview=_empty_overview(),
            equity=EquityResponse(points=[]),
            monthly=MonthlyResponse(years=[], grand_total=0.0),
        )

    df = pd.DataFrame(
        [
            {
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "pnl": t.pnl,
            }
            for t in trades
        ]
    )
    df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
    df = df.dropna(subset=["entry_time"])
    # Drop timezone so Period conversion stays quiet
    if getattr(df["entry_time"].dt, "tz", None) is not None:
        df["entry_time"] = df["entry_time"].dt.tz_localize(None)
    df["trade_date"] = df["entry_time"].dt.date

    total_trades = len(df)
    total_pnl = float(df["pnl"].sum())
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]
    win_trades = len(wins)
    loss_trades = len(losses)
    win_rate = round(win_trades / total_trades * 100, 3) if total_trades else 0.0

    avg_win = round(float(wins["pnl"].mean()), 2) if win_trades else 0.0
    avg_loss = round(float(losses["pnl"].mean()), 2) if loss_trades else 0.0

    daily = df.groupby("trade_date")["pnl"].sum().sort_index()
    total_days = len(daily)
    profit_days = int((daily > 0).sum())
    loss_days = int((daily <= 0).sum())
    profit_days_pct = round(profit_days / total_days * 100, 2) if total_days else 0.0

    avg_profit_on_profit_days = (
        round(float(daily[daily > 0].mean()), 2) if profit_days else 0.0
    )
    avg_loss_on_loss_days = (
        round(float(daily[daily <= 0].mean()), 2) if loss_days else 0.0
    )

    equity = daily.cumsum()
    drawdown = equity - equity.cummax()
    max_drawdown = round(float(drawdown.min()), 2) if len(drawdown) else 0.0

    # Top-5 drawdown troughs (distinct local minima approximation: sorted unique DDs)
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
    risk_reward = (
        round(abs(avg_win / avg_loss), 3) if avg_loss != 0 else float("inf")
    )
    if isinstance(risk_reward, float) and not math.isfinite(risk_reward):
        risk_reward = 0.0

    win_pct_frac = win_trades / total_trades if total_trades else 0.0
    loss_pct_frac = loss_trades / total_trades if total_trades else 0.0
    expectancy = round(win_pct_frac * avg_win + loss_pct_frac * avg_loss, 3)

    gross_wins = float(wins["pnl"].sum()) if win_trades else 0.0
    gross_losses = abs(float(losses["pnl"].sum())) if loss_trades else 0.0
    profit_factor = (
        round(gross_wins / gross_losses, 3) if gross_losses > 0 else 0.0
    )

    mean_daily = round(float(daily.mean()), 4) if total_days else 0.0
    std_dev = round(float(daily.std(ddof=0)), 4) if total_days else 0.0
    mean_std = round(mean_daily / std_dev, 4) if std_dev != 0 else 0.0
    sharpe = (
        round(mean_daily / std_dev * math.sqrt(252), 3) if std_dev != 0 else 0.0
    )
    sqn = (
        round(math.sqrt(total_trades) * (avg_pnl_per_trade / float(df["pnl"].std(ddof=0))), 2)
        if total_trades > 1 and float(df["pnl"].std(ddof=0)) != 0
        else 0.0
    )

    start_date: date | None = daily.index.min() if total_days else None
    end_date: date | None = daily.index.max() if total_days else None

    overview = OverviewResponse(
        total_pnl=round(total_pnl, 2),
        win_rate=win_rate,
        calmar=calmar,
        max_drawdown=max_drawdown,
        total_trades=total_trades,
        win_trades=win_trades,
        loss_trades=loss_trades,
        profit_days=profit_days,
        loss_days=loss_days,
        total_days=total_days,
        total_months=total_months,
        start_date=start_date,
        end_date=end_date,
        avg_monthly=avg_monthly,
        median_monthly=median_monthly,
        avg_weekly=avg_weekly,
        avg_win=avg_win,
        avg_loss=avg_loss,
        avg_pnl_per_trade=avg_pnl_per_trade,
        risk_reward=risk_reward,
        expectancy=expectancy,
        avg_profit_on_profit_days=avg_profit_on_profit_days,
        avg_loss_on_loss_days=avg_loss_on_loss_days,
        profit_days_pct=profit_days_pct,
        top5_dd_avg=top5_dd_avg,
        top5_ld_avg=top5_ld_avg,
        profit_factor=profit_factor,
        recovery_factor=recovery_factor,
        sortino=sortino,
        sharpe=sharpe,
        sqn=sqn,
        mean_daily=mean_daily,
        std_dev=std_dev,
        mean_std=mean_std,
    )

    equity_points = [
        EquityPoint(
            date=d,
            daily_pnl=round(float(daily.loc[d]), 2),
            equity=round(float(equity.loc[d]), 2),
            drawdown=round(float(drawdown.loc[d]), 2),
        )
        for d in daily.index
    ]

    monthly = _build_monthly(df, total_pnl)

    meta = SessionMeta(
        filename=filename,
        row_count=len(trades),
        start_date=start_date,
        end_date=end_date,
        original_headers=original_headers,
        column_map=column_map,
        loaded_at=loaded_at,
    )

    return AnalysisBundle(
        meta=meta,
        trades=trades,
        overview=overview,
        equity=EquityResponse(points=equity_points),
        monthly=monthly,
    )


def _build_monthly(df: pd.DataFrame, total_pnl: float) -> MonthlyResponse:
    df = df.copy()
    df["year"] = df["entry_time"].dt.year
    df["month_num"] = df["entry_time"].dt.month

    years_present = sorted(df["year"].unique().tolist())
    year_rows: list[MonthlyYearRow] = []

    for year in years_present:
        ydf = df[df["year"] == year]
        months: list[MonthCell] = []
        net = 0.0
        for m in range(1, 13):
            mdf = ydf[ydf["month_num"] == m]
            if mdf.empty:
                months.append(MonthCell(month=m, pnl=None, trade_count=0))
            else:
                pnl = round(float(mdf["pnl"].sum()), 2)
                months.append(MonthCell(month=m, pnl=pnl, trade_count=len(mdf)))
                net += pnl
        year_rows.append(
            MonthlyYearRow(year=int(year), months=months, net=round(net, 2))
        )

    return MonthlyResponse(years=year_rows, grand_total=round(float(total_pnl), 2))
