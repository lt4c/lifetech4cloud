
from __future__ import annotations

import secrets
import string
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User
from app.settings import get_settings

from ..deps import require_perm
from ..schemas import AssetUploadResponse
from ..services import assets as asset_service

ALLOWED_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(tags=["admin-assets"])


def _generate_code() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


@router.post("/assets/upload", response_model=AssetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    file: UploadFile = File(...),
    actor: User = Depends(require_perm("asset:upload")),
    db: Session = Depends(get_db),
) -> AssetUploadResponse:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type.")

    extension = ALLOWED_CONTENT_TYPES[content_type]

    def generator() -> str:
        return _generate_code()

    code = asset_service.generate_unique_code(db, generator)
    stored_name = f"{code}{extension}"
    stored_path = ASSETS_DIR / stored_name

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    with stored_path.open("wb") as buffer:
        buffer.write(data)

    asset = asset_service.create_asset(
        db,
        code=code,
        stored_path=stored_name,
        original_filename=file.filename,
        content_type=content_type,
        uploader=actor,
    )

    settings = get_settings()
    url = f"{settings.base_url.rstrip('/')}/assets/{asset.code}"
    return AssetUploadResponse(code=asset.code, url=url, content_type=asset.content_type)
