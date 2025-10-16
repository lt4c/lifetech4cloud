from __future__ import annotations

import hashlib

from fastapi import HTTPException, Request, status

from app.settings import get_settings


def compute_csrf_token(session_token: str, path: str) -> str:
    settings = get_settings()
    raw = f"{session_token}:{path}"
    return hashlib.sha256(f"{settings.secret_key}:{raw}".encode("utf-8")).hexdigest()


def enforce_csrf(request: Request) -> None:
    if request.method in {"GET", "OPTIONS", "HEAD"}:
        return
    settings = get_settings()
    session_token = request.cookies.get(settings.session_cookie_name, "")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing session for CSRF validation.")
    provided = request.headers.get("X-CSRF-Token") or request.headers.get("X-Csrf-Token")
    expected = compute_csrf_token(session_token, request.url.path)
    if not provided or provided != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token.")
