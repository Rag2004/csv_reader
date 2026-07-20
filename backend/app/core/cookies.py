"""HTTP-only cookie helpers for invisible multi-user sessions."""

from __future__ import annotations

from fastapi import Request, Response

from app.core.session import COOKIE_NAME, new_session_id


def read_session_id(request: Request) -> str | None:
    return request.cookies.get(COOKIE_NAME)


def resolve_or_create_session_id(request: Request) -> str:
    existing = read_session_id(request)
    return existing or new_session_id()


def set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")
