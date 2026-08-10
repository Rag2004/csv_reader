import { useEffect, useState } from 'react';
import { fetchMonthly, fetchOverview } from '../api/client';
import EmptyState from '../components/EmptyState';
import KpiCard from '../components/KpiCard';
import MonthlyHeatmap from '../components/MonthlyHeatmap';
import { fmtInt, fmtNumber, fmtPct, pnlClass } from '../utils/format';

export default function Overview({ hasSession }) {
  const [data, setData] = useState(null);
  const [monthly, setMonthly] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!hasSession) {
      setData(null);
      setMonthly(null);
      return;
    }
    Promise.all([fetchOverview(), fetchMonthly()])
      .then(([overview, monthlyData]) => {
        setData(overview);
        setMonthly(monthlyData);
      })
      .catch((e) => setError(e.message));
  }, [hasSession]);

  if (!hasSession) return <EmptyState />;
  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Loading…</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Overview</h1>
        <p>
          {data.start_date} → {data.end_date} · {fmtInt(data.total_trades)} trades
        </p>
      </div>

      <div className="kpi-strip">
        <div className="kpi-pill">
          <div className="label">Total P&amp;L</div>
          <div className={`value ${pnlClass(data.total_pnl)}`}>{fmtNumber(data.total_pnl)}</div>
        </div>
        <div className="kpi-pill">
          <div className="label">Win rate</div>
          <div className="value">{fmtPct(data.win_rate)}</div>
        </div>
        <div className="kpi-pill">
          <div className="label">Calmar</div>
          <div className="value">{fmtNumber(data.calmar)}</div>
        </div>
        <div className="kpi-pill">
          <div className="label">Max drawdown</div>
          <div className={`value ${pnlClass(data.max_drawdown)}`}>
            {fmtNumber(data.max_drawdown)}
          </div>
        </div>
      </div>

      <div className="card-grid">
        <KpiCard
          title="General statistics"
          rows={[
            ['Start Date', data.start_date || '—'],
            ['End Date', data.end_date || '—'],
            ['Total Trades', fmtInt(data.total_trades)],
            ['Total Days', fmtInt(data.total_days)],
            ['Total Months', fmtInt(data.total_months)],
            ['Profit Days', fmtInt(data.profit_days)],
            ['Loss Days', fmtInt(data.loss_days)],
          ]}
        />
        <KpiCard
          title="Profitability & drawdown"
          rows={[
            ['Net Profit', fmtNumber(data.total_pnl)],
            ['Avg Monthly', fmtNumber(data.avg_monthly)],
            ['Median Monthly', fmtNumber(data.median_monthly)],
            ['Avg Weekly', fmtNumber(data.avg_weekly)],
            ['Top 5 DD Avg', fmtNumber(data.top5_dd_avg)],
            ['Top 5 LD Avg', fmtNumber(data.top5_ld_avg)],
            ['Recovery Factor', fmtNumber(data.recovery_factor, 3)],
          ]}
        />
        <KpiCard
          title="Risk-adjusted ratios"
          rows={[
            ['Calmar', fmtNumber(data.calmar)],
            ['Sortino (monthly)', fmtNumber(data.sortino, 3)],
            ['Sharpe', fmtNumber(data.sharpe, 3)],
            ['Profit Factor', fmtNumber(data.profit_factor, 3)],
            ['Win Rate', fmtPct(data.win_rate)],
            ['Expectancy', fmtNumber(data.expectancy, 3)],
            ['Risk / Reward', fmtNumber(data.risk_reward, 3)],
          ]}
        />
        <KpiCard
          title="Trade & day averages"
          rows={[
            ['Avg Win', fmtNumber(data.avg_win)],
            ['Avg Loss', fmtNumber(data.avg_loss)],
            ['Avg / Trade', fmtNumber(data.avg_pnl_per_trade)],
            ['Avg Profit Day', fmtNumber(data.avg_profit_on_profit_days)],
            ['Avg Loss Day', fmtNumber(data.avg_loss_on_loss_days)],
            ['Profit Day %', fmtPct(data.profit_days_pct)],
            ['SQN', fmtNumber(data.sqn)],
          ]}
        />
      </div>

      <div className="panel" style={{ marginTop: '1.25rem' }}>
        <h2>Monthly P&amp;L</h2>
        {monthly ? (
          <MonthlyHeatmap years={monthly.years} grandTotal={monthly.grand_total} />
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>Loading monthly…</p>
        )}
      </div>
    </div>
  );
}
