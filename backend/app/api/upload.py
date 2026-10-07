"""Upload / load-path / session clear endpoints."""

from __future__ import annotations

import math
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field

from app.core.cookies import (
    clear_session_cookie,
    read_session_id,
    resolve_or_create_session_id,
    set_session_cookie,
)
from app.core.loader import CSVLoadError, load_csv_bytes, load_csv_path
from app.core.metrics import compute_analysis
from app.core.charges import apply_charges
from app.core.slippage import apply_slippage_pct
from app.core import session as session_store
from app.schemas.meta import display_filename
from app.schemas.responses import UploadResponse
from app.schemas.trades import NormalizedTrade

router = APIRouter(tags=["upload"])


def _safe_parent(path: Path, index: int) -> Path | None:
    try:
        return path.parents[index]
    except IndexError:
        return None


def _allowlist_roots() -> list[Path]:
    """Roots permitted for load-path / browse (works in monorepo and Docker)."""
    here = Path(__file__).resolve()
    # Docker: /app/app/api/upload.py → /app ; monorepo: …/csv_reader/backend/app/api/upload.py → csv_reader
    app_root = _safe_parent(here, 2)  # …/backend or /app
    module_root = _safe_parent(here, 3)  # …/csv_reader (monorepo only)
    repo_root = _safe_parent(here, 4)  # Quant_engine (monorepo only)

    roots: list[Path] = [
        Path.cwd(),
        Path.cwd() / "samples",
        Path.cwd() / "results",
        Path("/app/samples"),  # Docker image COPY samples
        Path("/app"),
    ]
    if app_root is not None:
        roots.extend([app_root, app_root / "samples", app_root / "results"])
    if module_root is not None:
        roots.extend([module_root, module_root / "samples", module_root / "results"])
    if repo_root is not None:
        roots.extend([repo_root, repo_root / "results", repo_root / "csv_reader" / "samples"])

    extra = os.environ.get("CSV_READER_ALLOW_ROOTS", "")
    for part in extra.split(os.pathsep):
        if part.strip():
            roots.append(Path(part.strip()))

    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        try:
            rr = r.resolve()
        except OSError:
            continue
        key = str(rr).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(rr)
    return out


def _is_allowed_path(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    # Allow selecting a run directory that contains run_manifest.json + trades.csv
    if resolved.is_dir() and (resolved / "run_manifest.json").is_file():
        trades = resolved / "trades.csv"
        if trades.is_file():
            resolved = trades.resolve()
        else:
            return False
    if not resolved.is_file() or resolved.suffix.lower() != ".csv":
        return False
    for root in _allowlist_roots():
        if not root.exists():
            continue
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


class LoadPathRequest(BaseModel):
    path: str = Field(..., description="Absolute or relative path under allowlisted roots")
    slippage_pct: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Adverse % applied to entry/exit prices by side (0–100); skipped if prices/side/qty missing",
    )
    brokerage_per_order: float = Field(
        0.0,
        ge=0.0,
        description="Brokerage in ₹ per order. 0 keeps raw PnL. A positive value also deducts STT and other charges; two orders are assumed per trade",
    )


class LoadPathsRequest(BaseModel):
    paths: list[str] = Field(..., min_length=1, description="One or more paths under allowlisted roots")
    slippage_pct: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Adverse % applied to entry/exit prices by side (0–100); skipped if prices/side/qty missing",
    )
    brokerage_per_order: float = Field(
        0.0,
        ge=0.0,
        description="Brokerage in ₹ per order. 0 keeps raw PnL. A positive value also deducts STT and other charges; two orders are assumed per trade",
    )


class BrowseResponse(BaseModel):
    roots: list[str]
    files: list[dict]


def _tag_source(trades: list[NormalizedTrade], source_file: str) -> list[NormalizedTrade]:
    out: list[NormalizedTrade] = []
    for t in trades:
        extras = dict(t.extras or {})
        extras["source_file"] = source_file
        out.append(t.model_copy(update={"extras": extras}))
    return out


def _combine_loaded(
    batches: list[tuple[list[NormalizedTrade], dict[str, str], list[str], str]],
) -> tuple[list[NormalizedTrade], dict[str, str], list[str], list[str]]:
    """Merge loaded CSV batches: concat trades, first column_map, union headers."""
    if not batches:
        return [], {}, [], []
    all_trades: list[NormalizedTrade] = []
    filenames: list[str] = []
    column_map = batches[0][1]
    header_seen: set[str] = set()
    headers: list[str] = []
    for trades, _cmap, file_headers, filename in batches:
        all_trades.extend(_tag_source(trades, filename))
        filenames.append(filename)
        for h in file_headers:
            if h not in header_seen:
                header_seen.add(h)
                headers.append(h)
    return all_trades, column_map, headers, filenames


def _validate_slippage_pct(slippage_pct: float) -> float:
    if slippage_pct < 0 or slippage_pct > 100:
        raise HTTPException(
            status_code=400,
            detail="slippage_pct must be between 0 and 100 inclusive",
        )
    return float(slippage_pct)


def _validate_brokerage_per_order(brokerage_per_order: float) -> float:
    if not math.isfinite(brokerage_per_order) or brokerage_per_order < 0:
        raise HTTPException(
            status_code=400,
            detail="brokerage_per_order must be a finite number >= 0",
        )
    return float(brokerage_per_order)


def _store_and_respond(
    response: Response,
    request: Request,
    trades,
    filename: str,
    headers: list[str],
    column_map: dict[str, str],
    slippage_pct: float = 0.0,
    brokerage_per_order: float = 0.0,
    filenames: list[str] | None = None,
) -> UploadResponse:
    session_id = resolve_or_create_session_id(request)
    file_list = list(filenames) if filenames else [filename]
    label = display_filename(file_list) or filename
    try:
        adjusted = apply_slippage_pct(trades, slippage_pct)
        adjusted = apply_charges(adjusted, brokerage_per_order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    bundle = compute_analysis(
        adjusted,
        filename=label,
        original_headers=headers,
        column_map=column_map,
        loaded_at=datetime.utcnow(),
        slippage_pct=slippage_pct,
        brokerage_per_order=brokerage_per_order,
        filenames=file_list,
    )
    session_store.set_bundle(session_id, bundle)
    set_session_cookie(response, session_id)
    return UploadResponse(meta=bundle.meta, overview=bundle.overview)


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    request: Request,
    response: Response,
    files: Annotated[list[UploadFile], File(description="One or more CSV files")],
    slippage_pct: float = Form(0.0),
    brokerage_per_order: float = Form(0.0),
):
    """Accept one or more CSVs (multipart field `files`, repeated)."""
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one .csv file.")

    slippage_pct = _validate_slippage_pct(slippage_pct)
    brokerage_per_order = _validate_brokerage_per_order(brokerage_per_order)

    batches: list[tuple[list[NormalizedTrade], dict[str, str], list[str], str]] = []
    for upload in files:
        name = upload.filename or "upload.csv"
        if not name.lower().endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail=f"Please upload .csv files only ({name}).",
            )
        data = await upload.read()
        if not data:
            raise HTTPException(status_code=400, detail=f"Uploaded file is empty: {name}")
        try:
            trades, column_map, headers = load_csv_bytes(data, filename=name)
        except CSVLoadError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"{name}: {exc.message}",
                    "headers_seen": exc.headers_seen,
                },
            ) from exc
        batches.append((trades, column_map, headers, name))

    all_trades, column_map, headers, filenames = _combine_loaded(batches)
    return _store_and_respond(
        response,
        request,
        all_trades,
        display_filename(filenames),
        headers,
        column_map,
        slippage_pct=slippage_pct,
        brokerage_per_order=brokerage_per_order,
        filenames=filenames,
    )


def _resolve_load_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() and path.exists():
        return path
    candidates = [
        Path.cwd() / path,
        Path.cwd() / "samples" / path.name,
        Path("/app/samples") / path.name,
        Path("/app") / path,
    ]
    for root in _allowlist_roots():
        candidates.append(root / path)
        candidates.append(root / path.name)
        candidates.append(root / "samples" / path.name)
        candidates.append(root / "results" / path.name)
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return path


def _load_one_allowed_path(raw_path: str) -> tuple[list[NormalizedTrade], dict[str, str], list[str], str]:
    """Resolve, allowlist, and load a single path. Raises HTTPException on failure."""
    from app.core.manifest import resolve_trades_path

    raw = Path(raw_path)
    if raw.exists() and raw.is_dir():
        path, _manifest = resolve_trades_path(raw)
    else:
        path = _resolve_load_path(raw_path)
        path, _manifest = resolve_trades_path(path)

    if not _is_allowed_path(path):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Path not allowed: {raw_path}. Place files under results/ or "
                "csv_reader/samples/, or set CSV_READER_ALLOW_ROOTS."
            ),
        )

    try:
        trades, column_map, headers, filename = load_csv_path(str(path))
    except CSVLoadError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"{raw_path}: {exc.message}",
                "headers_seen": exc.headers_seen,
            },
        ) from exc
    return trades, column_map, headers, filename


@router.post("/load-path", response_model=UploadResponse)
async def load_path(
    body: LoadPathRequest,
    request: Request,
    response: Response,
):
    trades, column_map, headers, filename = _load_one_allowed_path(body.path)
    tagged = _tag_source(trades, filename)
    return _store_and_respond(
        response,
        request,
        tagged,
        filename,
        headers,
        column_map,
        slippage_pct=body.slippage_pct,
        brokerage_per_order=body.brokerage_per_order,
        filenames=[filename],
    )


@router.post("/load-paths", response_model=UploadResponse)
async def load_paths(
    body: LoadPathsRequest,
    request: Request,
    response: Response,
):
    """Load and combine multiple allowlisted CSV paths into one analysis session."""
    slippage_pct = _validate_slippage_pct(body.slippage_pct)
    brokerage_per_order = _validate_brokerage_per_order(body.brokerage_per_order)

    batches: list[tuple[list[NormalizedTrade], dict[str, str], list[str], str]] = []
    for raw_path in body.paths:
        batches.append(_load_one_allowed_path(raw_path))

    all_trades, column_map, headers, filenames = _combine_loaded(batches)
    return _store_and_respond(
        response,
        request,
        all_trades,
        display_filename(filenames),
        headers,
        column_map,
        slippage_pct=slippage_pct,
        brokerage_per_order=brokerage_per_order,
        filenames=filenames,
    )


@router.get("/browse", response_model=BrowseResponse)
async def browse_files():
    """List CSV files under allowlisted roots for dashboard picker."""
    files: list[dict] = []
    roots_out: list[str] = []
    for root in _allowlist_roots():
        root = root.resolve()
        if not root.exists():
            continue
        roots_out.append(str(root))
        for p in sorted(root.rglob("*.csv")):
            item = {
                "path": str(p),
                "name": p.name,
                "folder": p.parent.name,
                "size": p.stat().st_size,
            }
            manifest = p.parent / "run_manifest.json"
            if p.name == "trades.csv" and manifest.is_file():
                item["has_manifest"] = True
                item["run_dir"] = str(p.parent)
            files.append(item)
    files = files[:500]
    return BrowseResponse(roots=roots_out, files=files)


@router.delete("/session")
async def clear_session(request: Request, response: Response):
    sid = read_session_id(request)
    ok = session_store.clear_bundle(sid)
    clear_session_cookie(response)
    return {"cleared": ok}
