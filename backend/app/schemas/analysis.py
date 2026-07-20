from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from .meta import SessionMeta
from .trades import NormalizedTrade


class OverviewResponse(BaseModel):
    total_pnl: float
    win_rate: float
    calmar: float
    max_drawdown: float
    total_trades: int
    win_trades: int
    loss_trades: int
    profit_days: int
    loss_days: int
    total_days: int
    total_months: int
    start_date: date | None = None
    end_date: date | None = None
    avg_monthly: float = 0.0
    median_monthly: float = 0.0
    avg_weekly: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_pnl_per_trade: float = 0.0
    risk_reward: float = 0.0
    expectancy: float = 0.0
    avg_profit_on_profit_days: float = 0.0
    avg_loss_on_loss_days: float = 0.0
    profit_days_pct: float = 0.0
    top5_dd_avg: float = 0.0
    top5_ld_avg: float = 0.0
    profit_factor: float = 0.0
    recovery_factor: float = 0.0
    sortino: float = 0.0
    sharpe: float = 0.0
    sqn: float = 0.0
    mean_daily: float = 0.0
    std_dev: float = 0.0
    mean_std: float = 0.0


class EquityPoint(BaseModel):
    date: date
    daily_pnl: float
    equity: float
    drawdown: float


class EquityResponse(BaseModel):
    points: list[EquityPoint] = Field(default_factory=list)


class MonthCell(BaseModel):
    month: int  # 1-12
    pnl: float | None = None
    trade_count: int = 0


class MonthlyYearRow(BaseModel):
    year: int
    months: list[MonthCell]
    net: float


class MonthlyResponse(BaseModel):
    years: list[MonthlyYearRow] = Field(default_factory=list)
    grand_total: float = 0.0


class AnalysisBundle(BaseModel):
    """Full precomputed analysis cached after upload."""

    meta: SessionMeta
    trades: list[NormalizedTrade]
    overview: OverviewResponse
    equity: EquityResponse
    monthly: MonthlyResponse
