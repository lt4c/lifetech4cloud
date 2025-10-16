from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.admin.audit import AuditContext, record_audit
from app.models import VpsProduct, Worker


class VpsProductService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_product(self, product_id: UUID) -> VpsProduct:
        product = self.db.get(VpsProduct, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return product

    def _resolve_workers(self, worker_ids: list[UUID]) -> list[Worker]:
        if not worker_ids:
            return []
        stmt = select(Worker).where(Worker.id.in_(worker_ids))
        workers = list(self.db.scalars(stmt))
        found_ids = {worker.id for worker in workers}
        missing = [str(worker_id) for worker_id in worker_ids if worker_id not in found_ids]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown worker ids: {', '.join(missing)}",
            )
        inactive = [worker for worker in workers if worker.status != "active"]
        if inactive:
            names = ", ".join(worker.name or str(worker.id) for worker in inactive)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Inactive workers: {names}",
            )
        return workers

    def get_product(self, product_id: UUID) -> VpsProduct:
        return self._get_product(product_id)

    def list_products(self, include_inactive: bool = True) -> list[VpsProduct]:
        stmt = select(VpsProduct).options(selectinload(VpsProduct.workers)).order_by(VpsProduct.created_at.desc())
        if not include_inactive:
            stmt = stmt.where(VpsProduct.is_active.is_(True))
        return list(self.db.scalars(stmt))

    def create_product(
        self,
        *,
        name: str,
        description: str | None,
        price_coins: int,
        provision_action: int,
        is_active: bool,
        worker_ids: list[UUID],
        context: AuditContext,
    ) -> VpsProduct:
        if price_coins < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="price_coins must be >= 0")
        product = VpsProduct(
            name=name.strip(),
            description=description,
            price_coins=price_coins,
            provision_action=provision_action,
            is_active=is_active,
        )
        workers = self._resolve_workers(worker_ids)
        product.workers = workers
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        record_audit(
            self.db,
            context=context,
            action="vps_product.create",
            target_type="vps_product",
            target_id=str(product.id),
            before=None,
            after={
                "name": product.name,
                "price_coins": product.price_coins,
                "provision_action": product.provision_action,
                "is_active": product.is_active,
            },
        )
        self.db.commit()
        return product

    def update_product(
        self,
        product_id: UUID,
        *,
        name: str | None,
        description: str | None,
        price_coins: int | None,
        provision_action: int | None,
        is_active: bool | None,
        worker_ids: list[UUID] | None,
        context: AuditContext,
    ) -> VpsProduct:
        product = self._get_product(product_id)
        created_at = product.created_at
        updated_at = product.updated_at
        before = {
            "name": product.name,
            "description": product.description,
            "price_coins": product.price_coins,
            "provision_action": product.provision_action,
            "is_active": product.is_active,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "provision_action": product.provision_action,
            "is_active": product.is_active,
        }
        if name is not None:
            product.name = name.strip()
        if description is not None:
            product.description = description
        if price_coins is not None:
            if price_coins < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="price_coins must be >= 0")
            product.price_coins = price_coins
        if provision_action is not None:
            product.provision_action = provision_action
        if is_active is not None:
            product.is_active = is_active
        if worker_ids is not None:
            product.workers = self._resolve_workers(worker_ids)
        product.updated_at = datetime.now(timezone.utc)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        after = {
            "name": product.name,
            "description": product.description,
            "price_coins": product.price_coins,
            "provision_action": product.provision_action,
            "is_active": product.is_active,
        }
        record_audit(
            self.db,
            context=context,
            action="vps_product.update",
            target_type="vps_product",
            target_id=str(product.id),
            before=before,
            after=after,
        )
        self.db.commit()
        return product

    def deactivate_product(self, product_id: UUID, *, context: AuditContext) -> VpsProduct:
        product = self._get_product(product_id)
        before = {"is_active": product.is_active}
        product.is_active = False
        product.updated_at = datetime.now(timezone.utc)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        record_audit(
            self.db,
            context=context,
            action="vps_product.deactivate",
            target_type="vps_product",
            target_id=str(product.id),
            before=before,
            after={"is_active": product.is_active},
        )
        self.db.commit()
        return product

    def delete_product(self, product_id: UUID, *, context: AuditContext) -> dict[str, object]:
        product = self._get_product(product_id)
        before = {
            "name": product.name,
            "description": product.description,
            "price_coins": product.price_coins,
            "provision_action": product.provision_action,
            "is_active": product.is_active,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "is_active": product.is_active,
        }
        target_id = str(product.id)
        self.db.delete(product)
        record_audit(
            self.db,
            context=context,
            action="vps_product.delete",
            target_type="vps_product",
            target_id=target_id,
            before=before,
            after=None,
        )
        self.db.commit()
        before_snapshot = {
            "id": target_id,
            "name": before["name"],
            "description": before["description"],
            "price_coins": before["price_coins"],
            "provision_action": before["provision_action"],
            "is_active": before["is_active"],
            "created_at": before["created_at"],
            "updated_at": before["updated_at"],
        }
        return before_snapshot
