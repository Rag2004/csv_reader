import { useEffect, useState } from 'react';
import { fetchEquity } from '../api/client';
import EmptyState from '../components/EmptyState';
import EquityChart from '../components/EquityChart';
import { fmtNumber } from '../utils/format';

export default function Equity({ hasSession }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!hasSession) {
      setData(null);
      return;
    }
    fetchEquity()
      .then(setData)
      .catch((e) => setError(e.message));
  }, [hasSession]);

  if (!hasSession) return <EmptyState />;
  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Loading…</p>;

  const points = data.points || [];
  const last = points[points.length - 1];
  const peak = points.reduce((m, p) => Math.max(m, p.equity), 0);
  const maxDd = points.reduce((m, p) => Math.min(m, p.drawdown), 0);

  return (
    <div>
      <div className="page-header">
        <h1>Equity &amp; Drawdown</h1>
        <p>Daily cumulative P&amp;L and underwater curve from cached analysis.</p>
      </div>

      <div className="kpi-strip" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div className="kpi-pill">
          <div className="label">Final equity</div>
          <div className="value">{fmtNumber(last?.equity ?? 0)}</div>
        </div>
        <div className="kpi-pill">
          <div className="label">Peak equity</div>
          <div className="value">{fmtNumber(peak)}</div>
        </div>
        <div className="kpi-pill">
          <div className="label">Max drawdown</div>
          <div className="value neg">{fmtNumber(maxDd)}</div>
        </div>
      </div>

      <EquityChart points={points} />
    </div>
  );
}
