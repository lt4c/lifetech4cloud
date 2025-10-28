from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.admin.deps import require_perm


router = APIRouter(tags=["admin-logs"], prefix="/logs")


LOG_FILE = Path(__file__).resolve().parent.parent.parent / "admin-actions.log"


@router.get("")
async def list_admin_logs(
    limit: int = Query(default=500, ge=1, le=5000),
    _: object = Depends(require_perm("role:read")),
) -> JSONResponse:
    if not LOG_FILE.exists():
        return JSONResponse({"items": []})
    try:
        # Tail last N lines efficiently
        lines: List[str] = []
        with open(LOG_FILE, "r", encoding="utf-8") as fp:
            fp.seek(0, os.SEEK_END)
            size = fp.tell()
            block = 4096
            buffer = ""
            while size > 0 and len(lines) < limit:
                read_size = block if size >= block else size
                fp.seek(size - read_size)
                data = fp.read(read_size)
                size -= read_size
                buffer = data + buffer
                while "\n" in buffer and len(lines) < limit:
                    idx = buffer.rfind("\n")
                    line = buffer[idx + 1 :]
                    buffer = buffer[:idx]
                    if line:
                        lines.append(line)
            if buffer and len(lines) < limit:
                lines.append(buffer)
        items = []
        for raw in reversed(lines):
            try:
                import json

                items.append(json.loads(raw))
            except Exception:
                continue
        return JSONResponse({"items": items})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"unable_to_read_logs: {exc}")


@router.post("")
async def append_admin_log(
    payload: dict,
    _: object = Depends(require_perm("role:update")),
) -> JSONResponse:
    try:
        import json
        os.makedirs(LOG_FILE.parent, exist_ok=True)
        record = {"ts": __import__("datetime").datetime.utcnow().isoformat(timespec="seconds") + "Z", **payload}
        with open(LOG_FILE, "a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        return JSONResponse({"success": True})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"unable_to_write_log: {exc}")


