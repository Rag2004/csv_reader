import { NavLink } from 'react-router-dom';
import CostDefaults from './CostDefaults';

export default function Sidebar({
  meta,
  slippagePct,
  chargePerTrade,
  onSlippageChange,
  onChargeChange,
  onPersistCosts,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">Quant Tools</div>
      <h1 className="sidebar-title">CSV Reader</h1>
      <nav>
        <NavLink to="/upload" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          Upload
        </NavLink>
        <NavLink to="/overview" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          Overview
        </NavLink>
        <NavLink to="/equity" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          Equity
        </NavLink>
        <NavLink to="/monthly" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          Monthly
        </NavLink>
        <NavLink to="/trades" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          Trades
        </NavLink>
      </nav>
      <CostDefaults
        slippagePct={slippagePct}
        chargePerTrade={chargePerTrade}
        onSlippageChange={onSlippageChange}
        onChargeChange={onChargeChange}
        onPersist={onPersistCosts}
      />
      <div className="session-chip">
        {meta ? (
          <>
            <strong>{meta.filename}</strong>
            {meta.row_count.toLocaleString()} trades
            {meta.start_date && meta.end_date ? (
              <div style={{ marginTop: 4 }}>
                {meta.start_date} → {meta.end_date}
              </div>
            ) : null}
          </>
        ) : (
          <>
            <strong>No file loaded</strong>
            Upload a CSV to begin
          </>
        )}
      </div>
    </aside>
  );
}
