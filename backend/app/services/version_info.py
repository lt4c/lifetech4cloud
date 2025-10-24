from __future__ import annotations

from datetime import datetime
from typing import Tuple
from uuid import UUID

VERSION_DESCRIPTIONS: dict[str, str] = {
    "dev": "Phien ban phat hanh som, chua duoc kiem thu on dinh.",
    "devStable": "Phien ban dang phat trien nhung da qua vong kiem thu hien tai.",
    "stable": "Phien ban on dinh da duoc kiem thu.",
    "devBack": "Phien ban cu duoc kich hoat lai do ban moi dang gap loi.",
}

DEFAULT_VERSION_ENTRY = {
    "channel": "dev",
    "version": "v0.0.0",
    "updated_at": None,
    "updated_by": None,
}

PLATFORM_VERSION_KEY = "platform.version"


def resolve_version_entry(value: dict) -> Tuple[str, str, str, datetime | None, UUID | None]:
    channel = value.get("channel") or DEFAULT_VERSION_ENTRY["channel"]
    version = value.get("version") or DEFAULT_VERSION_ENTRY["version"]
    description = VERSION_DESCRIPTIONS.get(channel, VERSION_DESCRIPTIONS["dev"])

    updated_at = None
    updated_raw = value.get("updated_at")
    if isinstance(updated_raw, str):
        try:
            updated_at = datetime.fromisoformat(updated_raw)
        except ValueError:
            updated_at = None

    updated_by = None
    updated_by_raw = value.get("updated_by")
    if isinstance(updated_by_raw, str):
        try:
            updated_by = UUID(updated_by_raw)
        except ValueError:
            updated_by = None

    return channel, version, description, updated_at, updated_by
