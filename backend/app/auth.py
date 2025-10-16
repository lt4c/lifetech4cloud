from __future__ import annotations

from typing import Any, Dict, TypedDict

import httpx
from fastapi import HTTPException, status

from .settings import Settings
from .utils import build_discord_avatar_url

AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
ME_URL = "https://discord.com/api/users/@me"


class DiscordUserResponse(TypedDict, total=False):
    id: str
    username: str
    global_name: str | None
    email: str | None
    avatar: str | None


class DiscordOAuthClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._timeout = httpx.Timeout(10.0, read=10.0)

    def build_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self.settings.discord_client_id,
            "redirect_uri": str(self.settings.discord_redirect_uri),
            "response_type": "code",
            "scope": self.settings.discord_scopes,
            "state": state,
            "prompt": "consent",
        }
        query = httpx.QueryParams(params)
        return f"{AUTHORIZE_URL}?{query}"

    async def exchange_code_for_token(self, code: str) -> str:
        payload = {
            "client_id": self.settings.discord_client_id,
            "client_secret": self.settings.discord_client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": str(self.settings.discord_redirect_uri),
            "scope": self.settings.discord_scopes,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    TOKEN_URL,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Discord token exchange request failed.",
            ) from exc
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for access token.",
            )
        data: Dict[str, Any] = response.json()
        access_token = data.get("access_token")
        token_type = data.get("token_type")
        if not access_token or token_type != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token response from Discord.",
            )
        return access_token

    async def fetch_current_user(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(ME_URL, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Discord userinfo request failed.",
            ) from exc
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user profile from Discord.",
            )
        payload: DiscordUserResponse = response.json()
        discord_id = payload.get("id")
        if not discord_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discord response missing user identifier.",
            )
        avatar_url = build_discord_avatar_url(discord_id, payload.get("avatar"))
        user_payload: Dict[str, Any] = {
            "discord_id": discord_id,
            "username": payload.get("username"),
            "display_name": payload.get("global_name"),
            "email": payload.get("email"),
            "avatar_url": avatar_url,
            "phone_number": None,  # Discord OAuth never exposes phone numbers.
        }
        return user_payload
