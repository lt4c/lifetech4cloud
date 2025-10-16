from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Announcement

router = APIRouter(prefix="/announcements", tags=["announcements"])


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class AnnouncementAttachmentPublic(BaseModel):
    label: str | None = None
    url: str


class AnnouncementSummaryPublic(BaseModel):
    id: UUID
    slug: str
    title: str
    excerpt: str | None = None
    hero_image_url: str | None = None
    created_at: str | None
    updated_at: str | None


class AnnouncementDetailPublic(AnnouncementSummaryPublic):
    content: str
    attachments: List[AnnouncementAttachmentPublic] = []


def _summary(record: Announcement) -> AnnouncementSummaryPublic:
    return AnnouncementSummaryPublic(
        id=record.id,
        slug=record.slug,
        title=record.title,
        excerpt=_clean_text(record.excerpt),
        hero_image_url=_clean_url(record.hero_image_url),
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


def _detail(record: Announcement) -> AnnouncementDetailPublic:
    attachments = [
        {"label": _clean_text(item.get("label")), "url": cleaned_url}
        for item in (record.attachments or [])
        if (cleaned_url := _clean_url(item.get("url")))
    ]
    return AnnouncementDetailPublic(
        **_summary(record).model_dump(),
        content=record.content,
        attachments=attachments,
    )


@router.get("", response_model=List[AnnouncementSummaryPublic])
async def list_announcements(db: Session = Depends(get_db)) -> List[AnnouncementSummaryPublic]:
    records = db.scalars(select(Announcement).order_by(Announcement.created_at.desc())).all()
    return [_summary(record) for record in records]


@router.get("/{announcement_id}", response_model=AnnouncementDetailPublic)
async def get_announcement(announcement_id: UUID, db: Session = Depends(get_db)) -> AnnouncementDetailPublic:
    record = db.get(Announcement, announcement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return _detail(record)


@router.get("/slug/{slug}", response_model=AnnouncementDetailPublic)
async def get_announcement_by_slug(slug: str, db: Session = Depends(get_db)) -> AnnouncementDetailPublic:
    stmt = select(Announcement).where(Announcement.slug == slug)
    record = db.scalars(stmt).first()
    if not record:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return _detail(record)
