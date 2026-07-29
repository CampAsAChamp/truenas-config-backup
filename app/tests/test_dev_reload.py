import asyncio
import os

import pytest

from src import config
from src.main import DOCS_DIR, STATIC_DIR, _static_url
from src.version import get_version


def test_static_url_uses_version_in_production_mode(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", False)

    assert _static_url("style.css") == f"/static/style.css?v={get_version()}"


def test_static_url_uses_mtime_in_dev_mode(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    style_path = os.path.join(STATIC_DIR, "style.css")
    expected_mtime = int(os.stat(style_path).st_mtime)

    assert _static_url("style.css") == f"/static/style.css?v={expected_mtime}"


def test_static_url_serves_brand_assets_from_docs(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", False)

    assert _static_url("logo.svg") == f"/brand/logo.svg?v={get_version()}"
    assert _static_url("logo.png") == f"/brand/logo.png?v={get_version()}"


def test_static_url_uses_docs_mtime_for_brand_assets_in_dev_mode(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    logo_path = os.path.join(DOCS_DIR, "logo.svg")
    expected_mtime = int(os.stat(logo_path).st_mtime)

    assert _static_url("logo.svg") == f"/brand/logo.svg?v={expected_mtime}"


def test_reload_events_disabled_without_dev_mode(client):
    response = client.get("/dev/reload-events", auth=None)

    assert response.status_code == 404


def test_dev_boot_id_disabled_without_dev_mode(client):
    response = client.get("/dev/boot-id", auth=None)

    assert response.status_code == 404


def test_dev_asset_versions_disabled_without_dev_mode(client):
    response = client.get("/dev/asset-versions", auth=None)

    assert response.status_code == 404


def test_dev_reload_state_disabled_without_dev_mode(client):
    response = client.get("/dev/reload-state", auth=None)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_reload_events_available_in_dev_mode():
    from unittest.mock import AsyncMock, MagicMock

    from src.dev_reload import BOOT_ID, reload_events

    request = MagicMock()
    request.is_disconnected = AsyncMock(return_value=False)

    response = await reload_events(request)

    assert response.media_type == "text/event-stream"
    assert response.headers["Cache-Control"] == "no-cache"

    first_chunk = await anext(response.body_iterator)
    assert first_chunk == "retry: 500\n\n"
    second_chunk = await anext(response.body_iterator)
    assert BOOT_ID in second_chunk


def test_dev_boot_id_returns_current_boot_id():
    import json

    from src.dev_reload import BOOT_ID, dev_boot_id

    payload = json.loads(dev_boot_id().body)

    assert payload == {"boot_id": BOOT_ID}


def test_dev_asset_versions_includes_static_assets():
    import json

    from src.dev_reload import dev_asset_versions

    payload = json.loads(dev_asset_versions().body)

    assert "style.css" in payload
    assert "js/app.js" in payload
    assert "js/dev-reload.js" in payload


def test_dev_reload_state_includes_boot_id_and_assets():
    import json

    from src.dev_reload import BOOT_ID, dev_reload_state

    payload = json.loads(dev_reload_state().body)

    assert payload["boot_id"] == BOOT_ID
    assert "style.css" in payload["assets"]
    assert "js/app.js" in payload["assets"]
    assert "js/dev-reload.js" in payload["assets"]


@pytest.mark.anyio
async def test_reload_events_exits_when_client_disconnects():
    from unittest.mock import MagicMock

    from src.dev_reload import BOOT_ID, reload_events

    request = MagicMock()
    call_count = 0

    async def is_disconnected():
        nonlocal call_count
        call_count += 1
        return call_count > 1

    request.is_disconnected = is_disconnected

    response = await reload_events(request)
    chunks = [chunk async for chunk in response.body_iterator]

    assert len(chunks) == 2
    assert chunks[0] == "retry: 500\n\n"
    assert BOOT_ID in chunks[1]


@pytest.mark.anyio
async def test_reload_events_exits_on_task_cancellation():
    from unittest.mock import AsyncMock, MagicMock, patch

    from src.dev_reload import reload_events

    request = MagicMock()
    request.is_disconnected = AsyncMock(return_value=False)

    response = await reload_events(request)

    with patch("src.dev_reload.asyncio.sleep", AsyncMock(side_effect=asyncio.CancelledError)):
        chunks = [chunk async for chunk in response.body_iterator]

    assert len(chunks) == 2
    assert chunks[0] == "retry: 500\n\n"
