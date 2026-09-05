import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { fmtNumber } from '../utils/format';

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: '#1a1a1f',
        border: '1px solid #2a2a32',
        padding: '8px 10px',
        borderRadius: 6,
        fontSize: 12,
      }}
    >
      <div style={{ marginBottom: 4, color: '#9a9aa3' }}>{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color || p.fill || '#e8e8ed' }}>
          {p.name}: {fmtNumber(p.value)}
        </div>
      ))}
    </div>
  );
}

export default function EquityChart({ points }) {
  const data = (points || []).map((p) => ({
    date: p.date,
    equity: p.equity,
    drawdown: p.drawdown,
    daily_pnl: p.daily_pnl,
  }));

  return (
    <>
      <div className="panel">
        <h2>Equity curve</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="eqFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3d9eff" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#3d9eff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#2a2a32" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: '#9a9aa3', fontSize: 11 }} minTickGap={40} />
              <YAxis tick={{ fill: '#9a9aa3', fontSize: 11 }} tickFormatter={(v) => fmtNumber(v, 0)} />
              <Tooltip content={<ChartTooltip />} />
              <Area
                type="monotone"
                dataKey="equity"
                name="Equity"
                stroke="#3d9eff"
                fill="url(#eqFill)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="panel">
        <h2>Drawdown</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="ddFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#e74c3c" stopOpacity={0.05} />
                  <stop offset="100%" stopColor="#e74c3c" stopOpacity={0.4} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#2a2a32" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: '#9a9aa3', fontSize: 11 }} minTickGap={40} />
              <YAxis tick={{ fill: '#9a9aa3', fontSize: 11 }} tickFormatter={(v) => fmtNumber(v, 0)} />
              <Tooltip content={<ChartTooltip />} />
              <Area
                type="monotone"
                dataKey="drawdown"
                name="Drawdown"
                stroke="#e74c3c"
                fill="url(#ddFill)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="panel">
        <h2>Daily PnL</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid stroke="#2a2a32" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: '#9a9aa3', fontSize: 11 }} minTickGap={40} />
              <YAxis tick={{ fill: '#9a9aa3', fontSize: 11 }} tickFormatter={(v) => fmtNumber(v, 0)} />
              <Tooltip content={<ChartTooltip />} />
              <ReferenceLine y={0} stroke="#5a5a66" />
              <Bar dataKey="daily_pnl" name="Daily PnL">
                {data.map((row) => (
                  <Cell
                    key={row.date}
                    fill={row.daily_pnl >= 0 ? '#2ecc71' : '#e74c3c'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
