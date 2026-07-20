import { useEffect, useState } from 'react';
import { fetchTrades } from '../api/client';
import EmptyState from '../components/EmptyState';
import { fmtNumber, pnlClass } from '../utils/format';

export default function Trades({ hasSession }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    pnl_sign: 'all',
    side: '',
    exit_type: '',
    symbol: '',
    offset: 0,
    limit: 100,
  });

  useEffect(() => {
    if (!hasSession) {
      setData(null);
      return;
    }
    const params = {
      offset: filters.offset,
      limit: filters.limit,
      pnl_sign: filters.pnl_sign,
      exit_type: filters.exit_type || undefined,
      symbol: filters.symbol || undefined,
    };
    if (filters.side !== '') params.side = filters.side;
    fetchTrades(params)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [hasSession, filters]);

  if (!hasSession) return <EmptyState />;
  if (error) return <div className="error-box">{error}</div>;

  const total = data?.total ?? 0;
  const page = Math.floor(filters.offset / filters.limit) + 1;
  const pages = Math.max(1, Math.ceil(total / filters.limit));

  return (
    <div>
      <div className="page-header">
        <h1>Trade history</h1>
        <p>{total.toLocaleString()} trades matching filters</p>
      </div>

      <div className="filters">
        <label>
          P&amp;L
          <select
            value={filters.pnl_sign}
            onChange={(e) => setFilters((f) => ({ ...f, pnl_sign: e.target.value, offset: 0 }))}
          >
            <option value="all">All</option>
            <option value="win">Wins</option>
            <option value="loss">Losses</option>
          </select>
        </label>
        <label>
          Side
          <select
            value={filters.side}
            onChange={(e) => setFilters((f) => ({ ...f, side: e.target.value, offset: 0 }))}
          >
            <option value="">All</option>
            <option value="1">Long</option>
            <option value="-1">Short</option>
          </select>
        </label>
        <label>
          Exit type
          <input
            value={filters.exit_type}
            onChange={(e) => setFilters((f) => ({ ...f, exit_type: e.target.value, offset: 0 }))}
            placeholder="Target, SL…"
          />
        </label>
        <label>
          Symbol
          <input
            value={filters.symbol}
            onChange={(e) => setFilters((f) => ({ ...f, symbol: e.target.value, offset: 0 }))}
            placeholder="Contains…"
          />
        </label>
      </div>

      <div className="panel" style={{ overflowX: 'auto' }}>
        {!data ? (
          <p style={{ color: 'var(--text-muted)' }}>Loading…</p>
        ) : (
          <table className="trades-table">
            <thead>
              <tr>
                <th>Entry</th>
                <th>Exit</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>P&amp;L</th>
                <th>Exit type</th>
                <th>Strategy</th>
              </tr>
            </thead>
            <tbody>
              {data.trades.map((t, i) => (
                <tr key={`${t.entry_time}-${i}`}>
                  <td>{t.entry_time?.replace('T', ' ').slice(0, 19)}</td>
                  <td>{t.exit_time ? t.exit_time.replace('T', ' ').slice(0, 19) : '—'}</td>
                  <td>{t.symbol || '—'}</td>
                  <td>{t.side === 1 ? 'Long' : t.side === -1 ? 'Short' : '—'}</td>
                  <td>{t.quantity ?? '—'}</td>
                  <td className={pnlClass(t.pnl)}>{fmtNumber(t.pnl)}</td>
                  <td>{t.exit_type || '—'}</td>
                  <td>{t.strategy || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', alignItems: 'center' }}>
          <button
            className="btn"
            disabled={filters.offset <= 0}
            onClick={() =>
              setFilters((f) => ({ ...f, offset: Math.max(0, f.offset - f.limit) }))
            }
          >
            Prev
          </button>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Page {page} / {pages}
          </span>
          <button
            className="btn"
            disabled={filters.offset + filters.limit >= total}
            onClick={() => setFilters((f) => ({ ...f, offset: f.offset + f.limit }))}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
