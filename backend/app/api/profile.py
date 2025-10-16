from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import UserProfile, UserProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


def _serialize_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        phone_number=user.phone_number,
        coins=user.coins or 0,
    )


@router.get("", response_model=UserProfile)
async def read_profile(current_user: User = Depends(get_current_user)) -> UserProfile:
    return _serialize_profile(current_user)


@router.patch("", response_model=UserProfile)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return _serialize_profile(current_user)

    changed = False
    if "display_name" in data:
        value = (data["display_name"] or "").strip()
        current_user.display_name = value or None
        changed = True

    if "phone_number" in data:
        value = (data["phone_number"] or "").strip()
        current_user.phone_number = value or None
        changed = True

    if not changed:
        return _serialize_profile(current_user)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _serialize_profile(current_user)


__all__ = ["router"]
