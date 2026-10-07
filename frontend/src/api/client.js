const API_BASE = '';

const defaultFetch = { credentials: 'include' };

async function parseError(res) {
  let detail = res.statusText;
  try {
    const body = await res.json();
    if (typeof body.detail === 'string') detail = body.detail;
    else if (body.detail?.message) detail = body.detail.message;
    else if (body.detail) detail = JSON.stringify(body.detail);
  } catch {
    /* ignore */
  }
  throw new Error(detail);
}

export async function fetchMeta() {
  const res = await fetch(`${API_BASE}/api/meta`, { ...defaultFetch });
  if (res.status === 404) return null;
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function uploadCsv(files, { slippage_pct = 0, brokerage_per_order = 0 } = {}) {
  const list = Array.isArray(files) ? files : files ? [files] : [];
  if (!list.length) throw new Error('Please select at least one .csv file');
  const form = new FormData();
  list.forEach((f) => form.append('files', f));
  form.append('slippage_pct', String(slippage_pct ?? 0));
  form.append('brokerage_per_order', String(brokerage_per_order ?? 0));
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    ...defaultFetch,
    body: form,
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function loadPath(path, { slippage_pct = 0, brokerage_per_order = 0 } = {}) {
  const res = await fetch(`${API_BASE}/api/load-path`, {
    method: 'POST',
    ...defaultFetch,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path,
      slippage_pct: Number(slippage_pct) || 0,
      brokerage_per_order: Number(brokerage_per_order) || 0,
    }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function loadPaths(paths, { slippage_pct = 0, brokerage_per_order = 0 } = {}) {
  const list = Array.isArray(paths) ? paths.filter(Boolean) : [];
  if (!list.length) throw new Error('Please select at least one path');
  const res = await fetch(`${API_BASE}/api/load-paths`, {
    method: 'POST',
    ...defaultFetch,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      paths: list,
      slippage_pct: Number(slippage_pct) || 0,
      brokerage_per_order: Number(brokerage_per_order) || 0,
    }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function browseFiles() {
  const res = await fetch(`${API_BASE}/api/browse`, { ...defaultFetch });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function clearSession() {
  const res = await fetch(`${API_BASE}/api/session`, {
    method: 'DELETE',
    ...defaultFetch,
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function fetchOverview() {
  const res = await fetch(`${API_BASE}/api/overview`, { ...defaultFetch });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function fetchEquity() {
  const res = await fetch(`${API_BASE}/api/equity`, { ...defaultFetch });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function fetchMonthly() {
  const res = await fetch(`${API_BASE}/api/monthly`, { ...defaultFetch });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function fetchTrades(params = {}) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'all') q.set(k, v);
  });
  const res = await fetch(`${API_BASE}/api/trades?${q}`, { ...defaultFetch });
  if (!res.ok) await parseError(res);
  return res.json();
}
