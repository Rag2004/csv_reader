import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  browseFiles,
  clearSession,
  loadPath,
  loadPaths,
  uploadCsv,
} from '../api/client';
import { fmtInt, fmtNumber } from '../utils/format';

function pickCsvFiles(fileList) {
  return Array.from(fileList || []).filter((f) =>
    (f.name || '').toLowerCase().endsWith('.csv'),
  );
}

export default function Upload({ meta, onLoaded, onCleared, slippagePct, brokeragePerOrder }) {
  const [dragOver, setDragOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [browse, setBrowse] = useState(null);
  const [pathInput, setPathInput] = useState('');
  const [selectedPaths, setSelectedPaths] = useState(() => new Set());
  const [lastUpload, setLastUpload] = useState(null);

  useEffect(() => {
    browseFiles()
      .then(setBrowse)
      .catch(() => setBrowse({ files: [], roots: [] }));
  }, []);

  const parseCosts = () => {
    const pct = Number(slippagePct);
    if (Number.isNaN(pct) || pct < 0 || pct > 100) {
      throw new Error('Slippage % must be between 0 and 100');
    }
    const brokerage = Number(brokeragePerOrder);
    if (!Number.isFinite(brokerage) || brokerage < 0) {
      throw new Error('Brokerage ₹ / order must be 0 or greater');
    }
    return { slippage_pct: pct, brokerage_per_order: brokerage };
  };

  const applyLoaded = (data) => {
    setLastUpload(data);
    const n = data.meta.filenames?.length || 1;
    setSuccess(
      `Loaded ${n} file${n === 1 ? '' : 's'} (${data.meta.filename}) — ${data.meta.row_count} trades`,
    );
    onLoaded?.(data.meta);
  };

  const handleFiles = useCallback(
    async (fileList) => {
      const csvs = pickCsvFiles(fileList);
      if (!csvs.length) {
        setError('Please select at least one .csv file');
        return;
      }
      setBusy(true);
      setError(null);
      setSuccess(null);
      try {
        const costs = parseCosts();
        const data = await uploadCsv(csvs, costs);
        applyLoaded(data);
      } catch (e) {
        setError(e.message || String(e));
      } finally {
        setBusy(false);
      }
    },
    [onLoaded, slippagePct, brokeragePerOrder],
  );

  const handlePath = async (path) => {
    if (!path?.trim()) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const costs = parseCosts();
      const data = await loadPath(path.trim(), costs);
      applyLoaded(data);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleCombineSelected = async () => {
    const paths = Array.from(selectedPaths);
    if (!paths.length) {
      setError('Select one or more files to combine');
      return;
    }
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const costs = parseCosts();
      const data = await loadPaths(paths, costs);
      applyLoaded(data);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  const togglePath = (path, e) => {
    e.stopPropagation();
    setSelectedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const handleClear = async () => {
    await clearSession();
    setLastUpload(null);
    setSuccess(null);
    setSelectedPaths(new Set());
    onCleared?.();
  };

  const displayMeta = lastUpload?.meta || meta;
  const fileCount = displayMeta?.filenames?.length || (displayMeta ? 1 : 0);

  return (
    <div>
      <div className="page-header">
        <h1>Upload</h1>
        <p>
          Load one or more trades CSVs. Multiple files are combined into one analysis
          (same-day P&amp;L adds). Column headers are matched case-insensitively.
        </p>
      </div>

      {error && <div className="error-box">{error}</div>}
      {success && <div className="success-box">{success}</div>}

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
            handleFiles(e.dataTransfer.files);
          }}
          onClick={() => document.getElementById('csv-input')?.click()}
        >
          <input
            id="csv-input"
            type="file"
            accept=".csv,text/csv"
            multiple
            onChange={(e) => {
              handleFiles(e.target.files);
              e.target.value = '';
            }}
          />
          <p style={{ margin: 0, fontSize: '1rem' }}>
            {busy ? 'Processing…' : 'Drop one or more CSVs here or click to browse'}
          </p>
          <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Expects P&amp;L + entry/exit time (e.g. Quant Engine trades.csv). Trades are combined.
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
          <button
            className="btn"
            disabled={busy || selectedPaths.size === 0}
            onClick={handleCombineSelected}
            title="Combine checked files into one analysis"
          >
            Combine selected ({selectedPaths.size})
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
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    checked={selectedPaths.has(f.path)}
                    onChange={(e) => togglePath(f.path, e)}
                    onClick={(e) => e.stopPropagation()}
                    aria-label={`Select ${f.name}`}
                  />
                  <span>
                    <span className="folder">{f.folder}/</span>
                    {f.name}
                  </span>
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
            {fileCount > 1 && (
              <>
                <dt>Files</dt>
                <dd>
                  <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
                    {(displayMeta.filenames || []).map((name) => (
                      <li key={name}>{name}</li>
                    ))}
                  </ul>
                </dd>
              </>
            )}
            <dt>Rows</dt>
            <dd>{fmtInt(displayMeta.row_count)}</dd>
            <dt>Date range</dt>
            <dd>
              {displayMeta.start_date || '—'} → {displayMeta.end_date || '—'}
            </dd>
            <dt>Brokerage ₹ / order</dt>
            <dd>{fmtNumber(displayMeta.brokerage_per_order ?? 0, 2)}</dd>
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
