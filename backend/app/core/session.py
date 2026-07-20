"""In-memory session store for AnalysisBundle (per cookie, multi-user safe)."""

from __future__ import annotations

import threading
import uuid

from app.schemas.analysis import AnalysisBundle

_lock = threading.Lock()
_sessions: dict[str, AnalysisBundle] = {}

COOKIE_NAME = "csv_reader_sid"


def new_session_id() -> str:
    return uuid.uuid4().hex


def set_bundle(session_id: str, bundle: AnalysisBundle) -> None:
    with _lock:
        _sessions[session_id] = bundle


def get_bundle(session_id: str | None) -> AnalysisBundle | None:
    """Return bundle for this session only — never fall back to another user."""
    if not session_id:
        return None
    with _lock:
        return _sessions.get(session_id)


def clear_bundle(session_id: str | None) -> bool:
    if not session_id:
        return False
    with _lock:
        if session_id not in _sessions:
            return False
        del _sessions[session_id]
        return True
