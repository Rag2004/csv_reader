"""Prefer canonical run manifests when loading from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_run_manifest(path: Path) -> dict[str, Any] | None:
    """Load run_manifest.json from a file path or its parent run directory."""
    candidates: list[Path] = []
    p = Path(path)
    if p.is_dir():
        candidates.append(p / "run_manifest.json")
    else:
        candidates.append(p.parent / "run_manifest.json")
        if p.name == "run_manifest.json":
            candidates.append(p)
    for cand in candidates:
        if cand.is_file():
            try:
                return json.loads(cand.read_text(encoding="utf-8"))
            except Exception:
                return None
    return None


def resolve_trades_path(path: Path) -> tuple[Path, dict[str, Any] | None]:
    """
    Resolve a user-supplied path to the trades CSV.

    If the path is a run directory (or a file inside one) with run_manifest.json,
    prefer the manifest's trades artifact (default trades.csv).
    """
    p = Path(path)
    manifest = load_run_manifest(p)
    if manifest is None:
        return p, None

    run_dir = p if p.is_dir() else p.parent
    artifacts = manifest.get("artifacts") or {}
    trades_meta = artifacts.get("trades") or {}
    rel = trades_meta.get("path") or "trades.csv"
    trades_path = run_dir / rel
    if trades_path.is_file():
        return trades_path, manifest
    fallback = run_dir / "trades.csv"
    if fallback.is_file():
        return fallback, manifest
    return p, manifest
