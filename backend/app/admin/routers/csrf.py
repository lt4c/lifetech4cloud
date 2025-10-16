from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.admin.admin_settings import get_admin_settings
from app.admin.deps import require_admin_user
from app.admin.schemas import CsrfTokenResponse
from app.admin.security import compute_csrf_token
from app.models import User
from app.settings import get_settings

router = APIRouter(tags=["admin-security"])


@router.get("/csrf-token", response_model=CsrfTokenResponse)
async def get_csrf_token(
    request: Request,
    path: str = Query(..., min_length=1),
    _: User = Depends(require_admin_user),
) -> CsrfTokenResponse:
    app_settings = get_settings()
    admin_settings = get_admin_settings()

    normalized = path if path.startswith("/") else f"/{path}"
    normalized = normalized.split("?", 1)[0].split("#", 1)[0]
    if not normalized.startswith(admin_settings.api_prefix):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path for CSRF token.",
        )

    session_token = request.cookies.get(app_settings.session_cookie_name)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing session for CSRF token.",
        )

    token = compute_csrf_token(session_token, normalized)
    return CsrfTokenResponse(token=token)
