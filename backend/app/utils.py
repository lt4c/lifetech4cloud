from __future__ import annotations

import secrets
from typing import Any, Dict

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from starlette.responses import Response

STATE_COOKIE_NAME = "discord_oauth_state"
STATE_MAX_AGE_SECONDS = 600
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
SESSION_SALT = "discord-login-session"
STATE_SALT = "discord-login-state"


def build_discord_avatar_url(discord_id: str, avatar_hash: str | None) -> str | None:
    if not avatar_hash:
        return "https://cdn.discordapp.com/embed/avatars/0.png"
    return f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png?size=256"


def _serializer(secret_key: str, salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret_key, salt=salt)


def generate_state_value() -> str:
    return secrets.token_urlsafe(32)


def sign_state(secret_key: str, state_value: str) -> str:
    return _serializer(secret_key, STATE_SALT).dumps({"state": state_value})


def verify_state(secret_key: str, token: str) -> str:
    data = _serializer(secret_key, STATE_SALT).loads(token, max_age=STATE_MAX_AGE_SECONDS)
    return str(data["state"])


def sign_session(secret_key: str, payload: Dict[str, Any]) -> str:
    return _serializer(secret_key, SESSION_SALT).dumps(payload)


def verify_session(secret_key: str, token: str) -> Dict[str, Any]:
    return _serializer(secret_key, SESSION_SALT).loads(token, max_age=SESSION_MAX_AGE_SECONDS)


def set_cookie(
    response: Response,
    *,
    name: str,
    value: str,
    secure: bool,
    max_age: int,
    httponly: bool = True,
) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        secure=secure,
        httponly=httponly,
        samesite="lax",
    )


def clear_cookie(response: Response, *, name: str) -> None:
    response.delete_cookie(key=name, samesite="lax")


def is_bad_signature(error: Exception) -> bool:
    return isinstance(error, (BadSignature, SignatureExpired))
