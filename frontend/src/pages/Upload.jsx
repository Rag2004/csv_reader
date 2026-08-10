import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  browseFiles,
  clearSession,
  loadPath,
  uploadCsv,
} from '../api/client';
import { fmtInt, fmtNumber } from '../utils/format';

export default function Upload({ meta, onLoaded, onCleared }) {
  const [dragOver, setDragOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [browse, setBrowse] = useState(null);
  const [pathInput, setPathInput] = useState('');
  const [lastUpload, setLastUpload] = useState(null);
  const [slippagePct, setSlippagePct] = useState(0);

  useEffect(() => {
    browseFiles()
      .then(setBrowse)
      .catch(() => setBrowse({ files: [], roots: [] }));
  }, []);

  const parseSlippage = () => {
    const n = Number(slippagePct);
    if (Number.isNaN(n) || n < 0 || n > 100) {
      throw new Error('Slippage % must be between 0 and 100');
    }
    return n;
  };

  const handleFile = useCallback(
    async (file) => {
      if (!file) return;
      setBusy(true);
      setError(null);
      setSuccess(null);
      try {
        const pct = parseSlippage();
        const data = await uploadCsv(file, { slippage_pct: pct });
        setLastUpload(data);
        setSuccess(`Loaded ${data.meta.filename} — ${data.meta.row_count} trades`);
        onLoaded?.(data.meta);
      } catch (e) {
        setError(e.message || String(e));
      } finally {
        setBusy(false);
      }
    },
    [onLoaded, slippagePct],
  );

  const handlePath = async (path) => {
    if (!path?.trim()) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const pct = parseSlippage();
      const data = await loadPath(path.trim(), { slippage_pct: pct });
      setLastUpload(data);
      setSuccess(`Loaded ${data.meta.filename} — ${data.meta.row_count} trades`);
      onLoaded?.(data.meta);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleClear = async () => {
    await clearSession();
    setLastUpload(null);
    setSuccess(null);
    onCleared?.();
  };

  const displayMeta = lastUpload?.meta || meta;

  return (
    <div>
      <div className="page-header">
        <h1>Upload</h1>
        <p>Load a trades CSV. Column headers are matched case-insensitively.</p>
      </div>

      {error && <div className="error-box">{error}</div>}
      {success && <div className="success-box">{success}</div>}

      <div className="panel">
        <h2>Costs</h2>
        <div className="filters">
          <label style={{ maxWidth: '12rem' }}>
            Slippage %
            <input
              type="number"
              min={0}
              max={100}
              step={0.1}
              value={slippagePct}
              onChange={(e) => setSlippagePct(e.target.value)}
              disabled={busy}
            />
          </label>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0.5rem 0 0' }}>
            Per trade: adjusted PnL = PnL − |PnL| × (slippage % / 100). Applied on upload / load.
          </p>
        </div>
      </div>

      <div className="panel">
        <h2>File upload</h2>
        <div
          className={`upload-zone${dragOver ? ' dragover' : ''}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const f = e.dataTransfer.files?.[0];
            handleFile(f);
          }}
          onClick={() => document.getElementById('csv-input')?.click()}
        >
          <input
            id="csv-input"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
          <p style={{ margin: 0, fontSize: '1rem' }}>
            {busy ? 'Processing…' : 'Drop a CSV here or click to browse'}
          </p>
          <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Expects P&amp;L + entry/exit time (e.g. Quant Engine trades.csv)
          </p>
        </div>
      </div>

      <div className="panel">
        <h2>Load from dashboard path</h2>
        <div className="filters">
          <label style={{ flex: 1 }}>
            Path
            <input
              value={pathInput}
              onChange={(e) => setPathInput(e.target.value)}
              placeholder="results/.../trades.csv or absolute path under allowlist"
            />
          </label>
          <button className="btn btn-primary" disabled={busy} onClick={() => handlePath(pathInput)}>
            Load path
          </button>
        </div>
        {browse?.files?.length ? (
          <div className="browse-list" style={{ marginTop: '0.75rem' }}>
            {browse.files.slice(0, 80).map((f) => (
              <div
                key={f.path}
                className="browse-item"
                onClick={() => {
                  setPathInput(f.path);
                  handlePath(f.path);
                }}
              >
                <span>
                  <span className="folder">{f.folder}/</span>
                  {f.name}
                </span>
                <span style={{ color: 'var(--text-muted)' }}>
                  {(f.size / 1024).toFixed(1)} KB
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No CSVs found under allowlisted roots yet.
          </p>
        )}
      </div>

      {displayMeta && (
        <div className="panel">
          <h2>File metadata</h2>
          <dl className="meta-grid">
            <dt>Filename</dt>
            <dd>{displayMeta.filename}</dd>
            <dt>Rows</dt>
            <dd>{fmtInt(displayMeta.row_count)}</dd>
            <dt>Date range</dt>
            <dd>
              {displayMeta.start_date || '—'} → {displayMeta.end_date || '—'}
            </dd>
            <dt>Slippage %</dt>
            <dd>{fmtNumber(displayMeta.slippage_pct ?? 0, 1)}</dd>
          </dl>

          <h2 style={{ marginTop: '1.25rem' }}>Detected column map</h2>
          <table className="map-table">
            <thead>
              <tr>
                <th>Logical field</th>
                <th>CSV header</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(displayMeta.column_map || {}).map(([k, v]) => (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2 style={{ marginTop: '1.25rem' }}>Original headers</h2>
          <p style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {(displayMeta.original_headers || []).join(', ')}
          </p>

          {lastUpload?.overview && (
            <p style={{ marginTop: '1rem' }}>
              Snapshot — Total P&amp;L{' '}
              <strong>{fmtNumber(lastUpload.overview.total_pnl)}</strong>
              {' · '}
              <Link to="/overview" style={{ color: 'var(--accent)' }}>
                Open Overview →
              </Link>
            </p>
          )}

          <div style={{ marginTop: '1rem' }}>
            <button className="btn" onClick={handleClear}>
              Clear data
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
