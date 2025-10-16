from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User
from app.settings import get_settings

from ..admin_settings import get_admin_settings
from ..deps import get_optional_current_user, require_perm
from ..schemas import UserQueryParams
from ..seed import bootstrap_secret_valid, grant_role_to_user, mark_bootstrap_consumed
from ..security import compute_csrf_token
from ..services import roles as role_service
from ..services import status as status_service
from ..services import users as user_service

TEMPLATES_PATH = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_PATH))

router = APIRouter(default_response_class=HTMLResponse)


def _csrf_token(request: Request, path: str) -> str:
    settings = get_settings()
    session_token = request.cookies.get(settings.session_cookie_name, "")
    return compute_csrf_token(session_token, path)


def _actor_context(request: Request, actor: User) -> dict[str, object]:
    return {
        "actor": actor,
        "csrf_token": _csrf_token(request, request.url.path),
    }


def _api_csrf(request: Request, path: str) -> str:
    return _csrf_token(request, path)


@router.get("/login")
async def login_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    settings = get_admin_settings()
    context = {"request": request, "settings": settings, "csrf_token": _csrf_token(request, request.url.path)}
    if not current_user:
        context["can_claim"] = bool(settings.default_password)
        return templates.TemplateResponse("login.html", context)

    admin_profile = user_service.get_user(db, current_user.id)
    context.update({"user": admin_profile})
    if any(role.name == "admin" for role in admin_profile.roles):
        return RedirectResponse(url=str(request.url_for("admin_users_page")), status_code=status.HTTP_302_FOUND)

    context["can_claim"] = bool(settings.default_password)
    return templates.TemplateResponse("login.html", context)


@router.post("/login")
async def login_claim_admin(
    request: Request,
    secret: str = Form(...),
    token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    if not current_user:
        return RedirectResponse(url=str(request.url_for("login_page")), status_code=status.HTTP_303_SEE_OTHER)
    expected_token = _csrf_token(request, request.url.path)
    if token != expected_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSRF token.")
    if not bootstrap_secret_valid(db, secret):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bootstrap secret.")
    grant_role_to_user(db, current_user, "admin")
    mark_bootstrap_consumed(db)
    return RedirectResponse(url=str(request.url_for("admin_users_page")), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/")
def admin_root() -> RedirectResponse:
    return RedirectResponse(url="users", status_code=status.HTTP_302_FOUND)


@router.get("/users", name="admin_users_page")
def users_page(
    request: Request,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
    role: str | None = None,
    actor: User = Depends(require_perm("user:read")),
    db: Session = Depends(get_db),
):
    role_uuid = None
    if role:
        try:
            role_uuid = UUID(role)
        except ValueError:
            role_uuid = None
    params = UserQueryParams(q=q, page=page, page_size=page_size, role=role_uuid)
    listing = user_service.list_users(db, params)
    settings = get_admin_settings()
    context = {
        "request": request,
        "listing": listing,
        "api_prefix": settings.api_prefix,
        **_actor_context(request, actor),
    }
    return templates.TemplateResponse("users.html", context)


@router.get("/users/{user_id}")
def user_detail_page(
    request: Request,
    user_id: str,
    actor: User = Depends(require_perm("user:read")),
    db: Session = Depends(get_db),
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    profile = user_service.get_user(db, user_uuid)
    roles = role_service.list_roles(db)
    settings = get_admin_settings()
    assign_csrf = _api_csrf(request, f"{settings.api_prefix}/users/{user_uuid}/roles")
    update_csrf = _api_csrf(request, f"{settings.api_prefix}/users/{user_uuid}")
    context = {
        "request": request,
        "profile": profile,
        "roles": roles,
        "api_prefix": settings.api_prefix,
        "assign_csrf": assign_csrf,
        "update_csrf": update_csrf,
        **_actor_context(request, actor),
    }
    return templates.TemplateResponse("user_detail.html", context)


@router.get("/roles")
def roles_page(
    request: Request,
    actor: User = Depends(require_perm("role:read")),
    db: Session = Depends(get_db),
):
    roles = role_service.list_roles(db)
    settings = get_admin_settings()
    available_permissions = role_service.list_all_permissions(db)
    context = {
        "request": request,
        "roles": roles,
        "available_permissions": available_permissions,
        "api_prefix": settings.api_prefix,
        "create_csrf": _api_csrf(request, f"{settings.api_prefix}/roles"),
        **_actor_context(request, actor),
    }
    return templates.TemplateResponse("roles.html", context)


@router.get("/roles/{role_id}")
def role_detail_page(
    request: Request,
    role_id: str,
    actor: User = Depends(require_perm("role:read")),
    db: Session = Depends(get_db),
):
    try:
        role_uuid = UUID(role_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    role = role_service.get_role(db, role_uuid)
    settings = get_admin_settings()
    perms_csrf = _api_csrf(request, f"{settings.api_prefix}/roles/{role_uuid}/perms")
    available_permissions = role_service.list_all_permissions(db)
    current_permission_codes = {perm.code for perm in role.permissions}
    context = {
        "request": request,
        "role": role,
        "api_prefix": settings.api_prefix,
        "perms_csrf": perms_csrf,
        "available_permissions": available_permissions,
        "current_permission_codes": current_permission_codes,
        **_actor_context(request, actor),
    }
    return templates.TemplateResponse("role_detail.html", context)


@router.get("/status")
def status_page(
    request: Request,
    actor: User = Depends(require_perm("sys:status:read")),
    db: Session = Depends(get_db),
):
    health = status_service.get_health_status()
    deps = status_service.get_dependency_status(db)
    db_status = status_service.get_db_status(db)
    settings = get_admin_settings()
    context = {
        "request": request,
        "health": health,
        "deps": deps,
        "db_status": db_status,
        "api_prefix": settings.api_prefix,
        **_actor_context(request, actor),
    }
    return templates.TemplateResponse("status.html", context)
