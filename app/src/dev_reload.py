"""Dev-only live reload support for local development.

Steps:
1. Generate a boot_id at import time (changes on each uvicorn restart).
2. Stream boot_id over SSE and expose a combined reload-state polling endpoint.
3. Browser clients reload when the server restarts or static assets change.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

BOOT_ID = uuid.uuid4().hex
HEARTBEAT_INTERVAL = 2
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

router = APIRouter()


def _static_asset_versions() -> dict[str, int]:
    versions: dict[str, int] = {}
    for root, _, files in os.walk(STATIC_DIR):
        for name in files:
            if not name.endswith((".css", ".js")):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, STATIC_DIR).replace(os.sep, "/")
            try:
                versions[rel] = int(os.stat(path).st_mtime)
            except OSError:
                versions[rel] = 0
    return versions


@router.get("/dev/boot-id")
def dev_boot_id():
    """Return the current process boot id (changes on each uvicorn restart)."""
    return JSONResponse({"boot_id": BOOT_ID})


@router.get("/dev/asset-versions")
def dev_asset_versions():
    """Return mtimes for static CSS/JS assets used to detect front-end edits."""
    return JSONResponse(_static_asset_versions())


@router.get("/dev/reload-state")
def dev_reload_state():
    """Return boot_id and static asset mtimes in one response for polling clients."""
    return JSONResponse({"boot_id": BOOT_ID, "assets": _static_asset_versions()})


@router.get("/dev/reload-events")
async def reload_events(request: Request):
    """Stream boot_id heartbeats so the browser can reload after server restarts."""

    async def event_stream():
        try:
            yield "retry: 500\n\n"
            while not await request.is_disconnected():
                payload = json.dumps({"boot_id": BOOT_ID})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(HEARTBEAT_INTERVAL)
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
