from __future__ import annotations

import importlib.metadata
import os
import shutil
import time
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..admin_settings import get_admin_settings
from ..cache import PermissionCache, get_permission_cache
from ..schemas import (
    DbStatusSlowQuery,
    StatusDbResponse,
    StatusDepsResponse,
    StatusHealthResponse,
)


def get_health_status() -> StatusHealthResponse:
    version = None
    try:
        version = importlib.metadata.version("discord-login-app")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover - local execution
        version = None
    build_time = os.getenv("BUILD_TIME")
    return StatusHealthResponse(api_up=True, version=version, build_time=build_time)


def _ping_database(db: Session) -> float | None:
    start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - database down
        return None
    end = time.perf_counter()
    return (end - start) * 1000


def _ping_redis(cache: PermissionCache) -> float | None:
    client = getattr(cache, "_redis", None)
    if client is None:
        return None
    start = time.perf_counter()
    try:
        client.ping()
    except Exception:  # pragma: no cover - redis unavailable
        return None
    end = time.perf_counter()
    return (end - start) * 1000


def get_dependency_status(db: Session) -> StatusDepsResponse:
    cache = get_permission_cache()
    db_ping_ms = _ping_database(db)
    redis_ping_ms = _ping_redis(cache)

    disk_free_mb = None
    try:
        usage = shutil.disk_usage("/")
        disk_free_mb = usage.free / (1024 * 1024)
    except Exception:  # pragma: no cover - platform specific
        disk_free_mb = None

    cpu_percent = None
    memory_percent = None
    try:
        import psutil  # type: ignore

        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
    except Exception:  # pragma: no cover - optional dependency
        cpu_percent = None
        memory_percent = None

    return StatusDepsResponse(
        db_ping_ms=db_ping_ms,
        redis_ping_ms=redis_ping_ms,
        disk_free_mb=disk_free_mb,
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
    )


def get_db_status(db: Session) -> StatusDbResponse:
    version = None
    try:
        version = db.scalar(text("SELECT version()"))
    except Exception:  # pragma: no cover - limited privileges
        version = None

    active_connections = None
    try:
        active_connections = db.scalar(
            text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
        )
    except Exception:  # pragma: no cover - limited privileges
        active_connections = None

    slow_queries: List[DbStatusSlowQuery] = []
    slow_query_sql = text(
        """
        SELECT query, EXTRACT(EPOCH FROM (now() - query_start)) * 1000 AS duration_ms
        FROM pg_stat_activity
        WHERE state != 'idle' AND now() - query_start > interval '1 seconds'
        ORDER BY duration_ms DESC
        LIMIT 5
        """
    )
    try:
        rows = db.execute(slow_query_sql)
        for query, duration_ms in rows:
            slow_queries.append(DbStatusSlowQuery(query=query[:500], duration_ms=float(duration_ms)))
    except Exception:  # pragma: no cover - permissions
        slow_queries = []

    last_migration = None
    try:
        last_migration = db.scalar(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
    except Exception:  # pragma: no cover - table missing
        last_migration = None

    return StatusDbResponse(
        version=version,
        active_connections=active_connections,
        slow_queries=slow_queries,
        last_migration=last_migration,
    )
