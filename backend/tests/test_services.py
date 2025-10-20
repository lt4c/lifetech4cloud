import asyncio
import hashlib
import hmac
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Configure environment for tests
os.environ.setdefault("DISCORD_CLIENT_ID", "123")
os.environ.setdefault("DISCORD_CLIENT_SECRET", "secret")
os.environ.setdefault("DISCORD_REDIRECT_URI", "https://example.com/callback")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test-service.db")
os.environ.setdefault("BASE_URL", "https://example.com")
os.environ.setdefault("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef")

from app.db import Base
from app.models import LedgerEntry, User, VpsProduct, Worker
from app.services.ads import AdsNonceError, AdsNonceManager, SSVSignatureVerifier
from app.services.wallet import WalletService
from app.services.vps import VpsService
from app.services.event_bus import SessionEventBus
from app.services.worker_client import WorkerClient


class DummyWorkerClient(WorkerClient):
    def __init__(self) -> None:
        # skip parent initialisation (no HTTP client needed)
        self.created: list[tuple[str, int]] = []
        self.stopped: list[str] = []
        self.logs: dict[str, str] = {}

    async def create_vm(self, *, worker, action: int):
        route = "test-route"
        self.created.append((str(worker.id), action))
        self.logs[route] = "log output"
        return route, f"{worker.base_url.rstrip('/')}/log/{route}"

    async def stop_vm(self, *, worker, route: str):
        self.stopped.append(route)

    async def fetch_log(self, *, worker, route: str) -> str:
        return self.logs.get(route, "")


class RecordingEventBus(SessionEventBus):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[tuple] = []

    async def publish(self, session_id, event):  # type: ignore[override]
        self.events.append((session_id, event))
        await super().publish(session_id, event)


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path/'service.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    try:
        with SessionLocal() as session:
            yield session
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_purchase_and_create_idempotent(db_session: Session):
    user = User(id=uuid4(), discord_id="d1", username="user", coins=100)
    db_session.add(user)

    worker = Worker(id=uuid4(), name="worker-1", base_url="http://worker", status="active", max_sessions=3)
    db_session.add(worker)

    product = VpsProduct(
        id=uuid4(),
        name="basic",
        price_coins=25,
        provision_action=1,
        is_active=True,
    )
    product.workers.append(worker)
    db_session.add(product)

    db_session.commit()

    event_bus = RecordingEventBus()
    service = VpsService(db_session, event_bus)
    client = DummyWorkerClient()
    wallet_service = WalletService(db_session)

    session, created = await service.purchase_and_create(
        user=user,
        product_id=product.id,
        idempotency_key="abc-123",
        worker_client=client,
        callback_base="https://backend",
    )
    assert created is True
    assert session.status == "provisioning"
    assert wallet_service.get_balance(user).balance == 75
    assert client.created, "Worker client should be invoked"

    session_second, created_second = await service.purchase_and_create(
        user=user,
        product_id=product.id,
        idempotency_key="abc-123",
        worker_client=client,
        callback_base="https://backend",
    )
    assert created_second is False
    assert session_second.id == session.id
    assert wallet_service.get_balance(user).balance == 75, "Coins should not be deducted twice"


def test_wallet_service_adjustments(db_session: Session):
    user = User(id=uuid4(), discord_id="wallet", username="wallet", coins=0)
    db_session.add(user)
    db_session.commit()

    wallet = WalletService(db_session)
    balance = wallet.adjust_balance(user, 10, entry_type="ads.reward", ref_id=None)
    assert balance.balance == 10
    assert user.coins == 10

    balance = wallet.adjust_balance(user, -3, entry_type="debit.test", ref_id=None)
    assert balance.balance == 7
    entries = db_session.execute(select(LedgerEntry).where(LedgerEntry.user_id == user.id)).scalars().all()
    assert len(entries) == 2
    assert {entry.type for entry in entries} == {"ads.reward", "debit.test"}

    with pytest.raises(HTTPException):
        wallet.adjust_balance(user, -100, entry_type="debit.fail", ref_id=None)


def test_ads_nonce_manager_roundtrip():
    manager = AdsNonceManager(ttl_seconds=30)
    user_id = uuid4()
    nonce = manager.issue(user_id, "device-hash", "earn")
    record = manager.consume(user_id, nonce)
    assert record.device_hash == "device-hash"
    assert record.placement == "earn"

    with pytest.raises(AdsNonceError):
        manager.consume(user_id, nonce)

    with pytest.raises(AdsNonceError):
        manager.consume(uuid4(), "missing")


def test_ssv_signature_verifier_hmac():
    settings = SimpleNamespace(ssv_secret="super-secret", ssv_public_key_path=None)
    verifier = SSVSignatureVerifier(settings)
    payload = "eventId=abc|uid=user|nonce=n-1|amount=5|duration=30|placement=earn|device=hash".encode()
    signature = hmac.new(settings.ssv_secret.encode(), payload, hashlib.sha256).hexdigest()

    verifier.verify(
        event_id="abc",
        uid="user",
        nonce="n-1",
        amount=5,
        duration=30,
        device_hash="hash",
        placement="earn",
        signature=signature,
    )

    with pytest.raises(HTTPException):
        verifier.verify(
            event_id="abc",
            uid="user",
            nonce="n-1",
            amount=5,
            duration=30,
            device_hash="hash",
            placement="earn",
            signature="deadbeef",
        )


def test_ssv_signature_requires_key():
    settings = SimpleNamespace(ssv_secret=None, ssv_public_key_path=None)
    verifier = SSVSignatureVerifier(settings)
    with pytest.raises(HTTPException):
        verifier.verify(
            event_id="abc",
            uid="user",
            nonce="n-1",
            amount=5,
            duration=30,
            device_hash="hash",
            placement="earn",
            signature="irrelevant",
        )
