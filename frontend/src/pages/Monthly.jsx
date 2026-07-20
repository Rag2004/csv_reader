import { useEffect, useState } from 'react';
import { fetchMonthly } from '../api/client';
import EmptyState from '../components/EmptyState';
import MonthlyHeatmap from '../components/MonthlyHeatmap';
import { fmtNumber, pnlClass } from '../utils/format';

export default function Monthly({ hasSession }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!hasSession) {
      setData(null);
      return;
    }
    fetchMonthly()
      .then(setData)
      .catch((e) => setError(e.message));
  }, [hasSession]);

  if (!hasSession) return <EmptyState />;
  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Loading…</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Monthly P&amp;L</h1>
        <p>
          Year × month heatmap · Grand total{' '}
          <span className={pnlClass(data.grand_total)} style={{ fontFamily: 'var(--mono)' }}>
            {fmtNumber(data.grand_total)}
          </span>
        </p>
      </div>

      <div className="panel">
        <h2>Heatmap</h2>
        <MonthlyHeatmap years={data.years} grandTotal={data.grand_total} />
      </div>
    </div>
  );
}
