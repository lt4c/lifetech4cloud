from __future__ import annotations

import re
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin.audit import AuditContext, record_audit
from app.admin.deps import require_perm
from app.admin.schemas import (
    AnnouncementCreateRequest,
    AnnouncementDetail,
    AnnouncementSummary,
    AnnouncementUpdateRequest,
)
from app.deps import get_db
from app.models import Announcement, User

router = APIRouter(tags=["admin-announcements"])

SLUG_PATTERN = re.compile(r"[^a-z0-9\-]+")


def _audit_context(request: Request, actor: User) -> AuditContext:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return AuditContext(actor_user_id=actor.id, ip=ip, ua=ua)


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


def _generate_slug(candidate: str, db: Session, *, exclude_id: UUID | None = None) -> str:
    base = candidate.strip().lower()
    base = SLUG_PATTERN.sub("-", base.replace(" ", "-"))
    slug = re.sub("-{2,}", "-", base).strip("-") or "announcement"
    if len(slug) > 191:
        slug = slug[:191].strip("-")
    unique_slug = slug
    suffix = 1
    while True:
        stmt = select(Announcement).where(Announcement.slug == unique_slug)
        if exclude_id:
            stmt = stmt.where(Announcement.id != exclude_id)
        exists = db.scalars(stmt).first()
        if not exists:
            return unique_slug
        suffix += 1
        candidate_slug = f"{slug}-{suffix}"
        unique_slug = candidate_slug[:191]


def _summary(record: Announcement) -> AnnouncementSummary:
    return AnnouncementSummary(
        id=record.id,
        slug=record.slug,
        title=record.title,
        excerpt=_clean_text(record.excerpt),
        hero_image_url=_clean_url(record.hero_image_url),
        created_at=record.created_at,
        updated_at=record.updated_at,
        created_by=record.created_by,
    )


def _detail(record: Announcement) -> AnnouncementDetail:
    return AnnouncementDetail(
        **_summary(record).model_dump(),
        content=record.content,
        attachments=[
            {
                "label": _clean_text(item.get("label")),
                "url": _clean_url(item.get("url")),
            }
            for item in (record.attachments or [])
            if _clean_url(item.get("url"))
        ],
    )


@router.get("/announcements", response_model=List[AnnouncementSummary])
async def list_announcements(
    _: User = Depends(require_perm("notification:read")),
    db: Session = Depends(get_db),
) -> List[AnnouncementSummary]:
    records = db.scalars(select(Announcement).order_by(Announcement.created_at.desc())).all()
    return [_summary(record) for record in records]


@router.get("/announcements/{announcement_id}", response_model=AnnouncementDetail)
async def get_announcement(
    announcement_id: UUID,
    _: User = Depends(require_perm("notification:read")),
    db: Session = Depends(get_db),
) -> AnnouncementDetail:
    record = db.get(Announcement, announcement_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    return _detail(record)


@router.post("/announcements", response_model=AnnouncementDetail, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    request: Request,
    payload: AnnouncementCreateRequest,
    actor: User = Depends(require_perm("notification:create")),
    db: Session = Depends(get_db),
) -> AnnouncementDetail:
    context = _audit_context(request, actor)

    slug_source = payload.slug or payload.title
    slug = _generate_slug(slug_source, db)

    record = Announcement(
        title=payload.title.strip(),
        slug=slug,
        message=payload.content,
        excerpt=_clean_text(payload.excerpt) or payload.content[:180],
        content=payload.content,
        hero_image_url=_clean_url(payload.hero_image_url),
        attachments=[
            {
                "label": _clean_text(attachment.label),
                "url": cleaned_url,
            }
            for attachment in payload.attachments
            if (cleaned_url := _clean_url(attachment.url))
        ],
        created_by=actor.id,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    record_audit(
        db,
        context=context,
        action="announcement.create",
        target_type="announcement",
        target_id=str(record.id),
        before=None,
        after=_detail(record).model_dump(),
    )
    db.commit()

    return _detail(record)


@router.patch("/announcements/{announcement_id}", response_model=AnnouncementDetail)
async def update_announcement(
    request: Request,
    announcement_id: UUID,
    payload: AnnouncementUpdateRequest,
    actor: User = Depends(require_perm("notification:update")),
    db: Session = Depends(get_db),
) -> AnnouncementDetail:
    record = db.get(Announcement, announcement_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    context = _audit_context(request, actor)
    before = _detail(record).model_dump()

    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"]:
        record.title = data["title"].strip()
    if "slug" in data and data["slug"]:
        record.slug = _generate_slug(data["slug"], db, exclude_id=record.id)
    if "excerpt" in data:
        record.excerpt = _clean_text(data["excerpt"])
    if "content" in data and data["content"]:
        record.content = data["content"]
        record.message = data["content"]
    if "hero_image_url" in data:
        record.hero_image_url = _clean_url(data["hero_image_url"])
    if "attachments" in data and data["attachments"] is not None:
        record.attachments = [
            {
                "label": _clean_text(item.label),
                "url": cleaned_url,
            }
            for item in (payload.attachments or [])
            if (cleaned_url := _clean_url(item.url))
        ]

    db.add(record)
    db.commit()
    db.refresh(record)

    record_audit(
        db,
        context=context,
        action="announcement.update",
        target_type="announcement",
        target_id=str(record.id),
        before=before,
        after=_detail(record).model_dump(),
    )
    db.commit()

    return _detail(record)


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: UUID,
    request: Request,
    actor: User = Depends(require_perm("notification:delete")),
    db: Session = Depends(get_db),
) -> Response:
    record = db.get(Announcement, announcement_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    context = _audit_context(request, actor)
    before = _detail(record).model_dump()

    db.delete(record)
    db.commit()

    record_audit(
        db,
        context=context,
        action="announcement.delete",
        target_type="announcement",
        target_id=str(announcement_id),
        before=before,
        after=None,
    )
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
