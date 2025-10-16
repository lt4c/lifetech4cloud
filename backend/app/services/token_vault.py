from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdminToken
from app.security.crypto import decrypt_secret, encrypt_secret

from app.admin.audit import AuditContext, record_audit


class TokenVaultService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tokens(self) -> list[AdminToken]:
        stmt = select(AdminToken).order_by(AdminToken.created_at.desc())
        return list(self.db.scalars(stmt))

    def create_token(
        self,
        *,
        label: str,
        token_plain: str,
        creator_user_id: UUID | None,
        context: AuditContext,
    ) -> AdminToken:
        if not token_plain:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token cannot be empty.")
        record = AdminToken(
            label=label,
            token_ciphertext=encrypt_secret(token_plain),
            token_prefix=token_plain[:4],
            created_by=creator_user_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        record_audit(
            self.db,
            context=context,
            action="admin.token.create",
            target_type="admin_token",
            target_id=str(record.id),
            before=None,
            after={"label": record.label, "token_prefix": record.token_prefix},
        )
        self.db.commit()
        return record

    def revoke_token(self, token_id: UUID, *, context: AuditContext) -> AdminToken:
        token = self.db.get(AdminToken, token_id)
        if not token:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found.")
        if token.revoked_at:
            return token
        before = {"revoked_at": token.revoked_at.isoformat() if token.revoked_at else None}
        token.revoked_at = datetime.now(timezone.utc)
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        record_audit(
            self.db,
            context=context,
            action="admin.token.revoke",
            target_type="admin_token",
            target_id=str(token.id),
            before=before,
            after={"revoked_at": token.revoked_at.isoformat()},
        )
        self.db.commit()
        return token

    def get_token_secret(self, token_id: UUID) -> str:
        token = self.db.get(AdminToken, token_id)
        if not token:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found.")
        return decrypt_secret(token.token_ciphertext)

