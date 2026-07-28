"""Dev-only live reload support for local development.

Steps:
1. Generate a boot_id at import time (changes on each uvicorn restart).
2. Expose GET /dev/reload-events as an SSE stream with periodic heartbeats.
3. Browser clients detect boot_id changes and reload the page automatically.
"""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

BOOT_ID = uuid.uuid4().hex

router = APIRouter()


@router.get("/dev/reload-events")
async def reload_events():
    """Stream boot_id heartbeats so the browser can reload after server restarts."""

    async def event_stream():
        while True:
            payload = json.dumps({"boot_id": BOOT_ID})
            yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
