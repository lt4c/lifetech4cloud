import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
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
from app.models import User, VpsProduct, Worker
from app.services.ads import AdsNonceManager, AdsService
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
    with SessionLocal() as session:
        yield session
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

    session, created = await service.purchase_and_create(
        user=user,
        product_id=product.id,
        idempotency_key="abc-123",
        worker_client=client,
        callback_base="https://backend",
    )
    assert created is True
    assert session.status == "provisioning"
    assert user.coins == 75
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
    assert user.coins == 75, "Coins should not be deducted twice"


def test_ads_service_claim(db_session: Session):
    user = User(id=uuid4(), discord_id="d2", username="ads-user", coins=0)
    db_session.add(user)
    db_session.commit()

    nonce_manager = AdsNonceManager(ttl_seconds=60)
    service = AdsService(db_session, nonce_manager)

    nonce = service.start(user)
    claim = service.claim(
        user,
        nonce=nonce,
        provider="adsense",
        proof={"token": "abcdef123456", "value": 5},
    )
    assert claim.value_coins == 5
    assert user.coins == 5
    assert claim.provider == "adsense"


