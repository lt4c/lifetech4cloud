
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, User


def generate_unique_code(db: Session, generator) -> str:
    while True:
        code = generator()
        exists = db.scalar(select(Asset).where(Asset.code == code))
        if not exists:
            return code


def create_asset(
    db: Session,
    *,
    code: str,
    stored_path: str,
    original_filename: str | None,
    content_type: str,
    uploader: User | None,
) -> Asset:
    asset = Asset(
        code=code,
        stored_path=stored_path,
        original_filename=original_filename,
        content_type=content_type,
        uploaded_by=uploader.id if uploader else None,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_asset_by_code(db: Session, code: str) -> Asset | None:
    return db.scalar(select(Asset).where(Asset.code == code))
