const STORAGE_KEY = 'csv_reader_cost_defaults';

export function loadCostDefaults() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { slippage_pct: 0, charge_per_trade: 0 };
    }
    const parsed = JSON.parse(raw);
    const slippage_pct = Number(parsed.slippage_pct);
    const charge_per_trade = Number(parsed.charge_per_trade);
    return {
      slippage_pct: Number.isFinite(slippage_pct) && slippage_pct >= 0 ? slippage_pct : 0,
      charge_per_trade:
        Number.isFinite(charge_per_trade) && charge_per_trade >= 0 ? charge_per_trade : 0,
    };
  } catch {
    return { slippage_pct: 0, charge_per_trade: 0 };
  }
}

export function saveCostDefaults({ slippage_pct, charge_per_trade }) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      slippage_pct: Number(slippage_pct) || 0,
      charge_per_trade: Number(charge_per_trade) || 0,
    }),
  );
}
