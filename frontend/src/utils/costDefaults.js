const STORAGE_KEY = 'csv_reader_cost_defaults';

export function loadCostDefaults() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { slippage_pct: 0, brokerage_per_order: 10 };
    }
    const parsed = JSON.parse(raw);
    const slippage_pct = Number(parsed.slippage_pct);
    const brokerage_per_order = Number(parsed.brokerage_per_order);
    return {
      slippage_pct: Number.isFinite(slippage_pct) && slippage_pct >= 0 ? slippage_pct : 0,
      brokerage_per_order:
        Number.isFinite(brokerage_per_order) && brokerage_per_order >= 0
          ? brokerage_per_order
          : 10,
    };
  } catch {
    return { slippage_pct: 0, brokerage_per_order: 10 };
  }
}

export function saveCostDefaults({ slippage_pct, brokerage_per_order }) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      slippage_pct: Number(slippage_pct) || 0,
      brokerage_per_order: Number(brokerage_per_order) || 0,
    }),
  );
}
