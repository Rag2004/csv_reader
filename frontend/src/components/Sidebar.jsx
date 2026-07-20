import { NavLink } from 'react-router-dom';

export default function Sidebar({ meta }) {
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
