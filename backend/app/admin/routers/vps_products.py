from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin.audit import AuditContext
from app.admin.deps import require_perm
from app.admin.schemas import (
    VpsProductCreateRequest,
    VpsProductDTO,
    VpsProductUpdateRequest,
    WorkerListItem,
)
from app.deps import get_db
from app.models import User, VpsProduct, Worker, VpsSession
from app.services.vps_products import VpsProductService


router = APIRouter(tags=["admin-vps-products"])


ACTIVE_STATUSES = {"pending", "provisioning", "ready"}


def _active_session_counts(db: Session, worker_ids: set[UUID]) -> dict[UUID, int]:
    if not worker_ids:
        return {}
    stmt = (
        select(VpsSession.worker_id, func.count(VpsSession.id))
        .where(VpsSession.worker_id.in_(worker_ids))
        .where(VpsSession.status.in_(ACTIVE_STATUSES))
        .group_by(VpsSession.worker_id)
    )
    return {row[0]: row[1] for row in db.execute(stmt).all()}


def _worker_item(worker: Worker, counts: dict[UUID, int]) -> WorkerListItem:
    return WorkerListItem(
        id=worker.id,
        name=worker.name,
        base_url=worker.base_url,
        status=worker.status,
        max_sessions=worker.max_sessions,
        active_sessions=counts.get(worker.id, 0),
        created_at=worker.created_at,
        updated_at=worker.updated_at,
    )


def _audit_context(request: Request, actor: User) -> AuditContext:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return AuditContext(actor_user_id=actor.id, ip=client_host, ua=user_agent)


def _dto(product: VpsProduct, counts: dict[UUID, int]) -> VpsProductDTO:
    worker_items = [_worker_item(worker, counts) for worker in product.workers]
    return VpsProductDTO(
        id=product.id,
        name=product.name,
        description=product.description,
        price_coins=product.price_coins,
        provision_action=product.provision_action,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        workers=worker_items,
    )


@router.get("/vps-products", response_model=list[VpsProductDTO])
async def list_products(
    include_inactive: bool = Query(True),
    _: User = Depends(require_perm("vps_product:read")),
    db: Session = Depends(get_db),
) -> list[VpsProductDTO]:
    service = VpsProductService(db)
    products = service.list_products(include_inactive=include_inactive)
    worker_ids = {worker.id for product in products for worker in product.workers}
    counts = _active_session_counts(db, worker_ids)
    return [_dto(product, counts) for product in products]


@router.post("/vps-products", response_model=VpsProductDTO, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: Request,
    payload: VpsProductCreateRequest,
    actor: User = Depends(require_perm("vps_product:create")),
    db: Session = Depends(get_db),
) -> VpsProductDTO:
    service = VpsProductService(db)
    context = _audit_context(request, actor)
    product = service.create_product(
        name=payload.name,
        description=payload.description,
        price_coins=payload.price_coins,
        provision_action=payload.provision_action,
        is_active=payload.is_active,
        worker_ids=payload.worker_ids,
        context=context,
    )
    counts = _active_session_counts(db, {worker.id for worker in product.workers})
    return _dto(product, counts)


@router.patch("/vps-products/{product_id}", response_model=VpsProductDTO)
async def update_product(
    request: Request,
    product_id: UUID,
    payload: VpsProductUpdateRequest,
    actor: User = Depends(require_perm("vps_product:update")),
    db: Session = Depends(get_db),
) -> VpsProductDTO:
    service = VpsProductService(db)
    context = _audit_context(request, actor)
    product = service.update_product(
        product_id,
        name=payload.name,
        description=payload.description,
        price_coins=payload.price_coins,
        provision_action=payload.provision_action,
        is_active=payload.is_active,
        worker_ids=payload.worker_ids,
        context=context,
    )
    counts = _active_session_counts(db, {worker.id for worker in product.workers})
    return _dto(product, counts)


@router.delete("/vps-products/{product_id}", response_model=VpsProductDTO)
async def deactivate_product(
    request: Request,
    product_id: UUID,
    actor: User = Depends(require_perm("vps_product:delete")),
    permanent: bool = Query(False),
    db: Session = Depends(get_db),
) -> VpsProductDTO:
    service = VpsProductService(db)
    context = _audit_context(request, actor)
    if permanent:
        service.delete_product(product_id, context=context)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    product = service.deactivate_product(product_id, context=context)
    counts = _active_session_counts(db, {worker.id for worker in product.workers})
    return _dto(product, counts)
