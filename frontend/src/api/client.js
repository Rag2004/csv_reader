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

export async function uploadCsv(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    ...defaultFetch,
    body: form,
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function loadPath(path) {
  const res = await fetch(`${API_BASE}/api/load-path`, {
    method: 'POST',
    ...defaultFetch,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
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
