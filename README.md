# CSV Reader — Trade Analytics Workstation

Independent full-stack module. Does **not** import from Quant Engine packages.

Multi-user safe: each browser gets an invisible HTTP-only cookie so uploads do not overwrite each other. No session ID in the UI or URL.

## Docker (recommended — share one link)

From the `csv_reader/` folder:

```bash
docker compose up --build
```

Open **http://\<server-ip\>:8080** and share that link. Each user uploads their own CSV and sees their own results.

```bash
# from repo root
docker compose -f csv_reader/docker-compose.yml up --build
```

Container restart clears in-memory analysis caches (users re-upload).

## Local development

### Backend (port 8100)

```bash
cd csv_reader/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8100
```

### Frontend (port 5174)

```bash
cd csv_reader/frontend
npm install
npm run dev
```

Open http://localhost:5174 (Vite proxies `/api` to the backend; cookies work via the proxy).

## Features

- Smart case-insensitive CSV column mapping
- Metrics computed once on upload and cached per browser cookie
- Optional costs on upload: flat ₹ per-trade charge and adverse entry/exit price slippage % (by side)
- Pages: Upload, Overview, Equity, Monthly heatmap, Trades
- Typed Pydantic API (`/api/meta`, `/api/overview`, `/api/equity`, `/api/monthly`, `/api/trades`)

## Allowlisted paths for “Load from dashboard”

- `csv_reader/samples/`
- `results/` (repo root)
- Extra roots via env `CSV_READER_ALLOW_ROOTS` (OS path separator)
