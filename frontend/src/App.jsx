import { useCallback, useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { fetchMeta } from './api/client';
import Sidebar from './components/Sidebar';
import { loadCostDefaults, saveCostDefaults } from './utils/costDefaults';
import Upload from './pages/Upload';
import Overview from './pages/Overview';
import Equity from './pages/Equity';
import Monthly from './pages/Monthly';
import Trades from './pages/Trades';

function AppShell() {
  const [meta, setMeta] = useState(null);
  const [costDefaults, setCostDefaults] = useState(() => loadCostDefaults());

  const updateCostDefaults = useCallback((patch) => {
    setCostDefaults((prev) => ({ ...prev, ...patch }));
  }, []);

  const persistCostDefaults = useCallback(() => {
    setCostDefaults((prev) => {
      const normalized = {
        slippage_pct: Number(prev.slippage_pct) || 0,
        brokerage_per_order: Number(prev.brokerage_per_order) || 0,
      };
      saveCostDefaults(normalized);
      return normalized;
    });
  }, []);

  const refreshMeta = useCallback(() => {
    fetchMeta()
      .then((m) => setMeta(m))
      .catch(() => setMeta(null));
  }, []);

  useEffect(() => {
    refreshMeta();
  }, [refreshMeta]);

  const hasSession = Boolean(meta);

  return (
    <div className="app">
      <Sidebar
        meta={meta}
        slippagePct={costDefaults.slippage_pct}
        brokeragePerOrder={costDefaults.brokerage_per_order}
        onSlippageChange={(value) => updateCostDefaults({ slippage_pct: value })}
        onBrokerageChange={(value) => updateCostDefaults({ brokerage_per_order: value })}
        onPersistCosts={persistCostDefaults}
      />
      <main className="main">
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route
            path="/upload"
            element={
              <Upload
                meta={meta}
                slippagePct={costDefaults.slippage_pct}
                brokeragePerOrder={costDefaults.brokerage_per_order}
                onLoaded={(m) => setMeta(m)}
                onCleared={() => setMeta(null)}
              />
            }
          />
          <Route path="/overview" element={<Overview hasSession={hasSession} />} />
          <Route path="/equity" element={<Equity hasSession={hasSession} />} />
          <Route path="/monthly" element={<Monthly hasSession={hasSession} />} />
          <Route path="/trades" element={<Trades hasSession={hasSession} />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
