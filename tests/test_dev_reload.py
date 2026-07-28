import os

import pytest

from app import config
from app.main import STATIC_DIR, _static_url
from app.version import get_version


def test_static_url_uses_version_in_production_mode(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", False)

    assert _static_url("style.css") == f"/static/style.css?v={get_version()}"


def test_static_url_uses_mtime_in_dev_mode(monkeypatch):
    monkeypatch.setattr(config, "DEV_MODE", True)
    style_path = os.path.join(STATIC_DIR, "style.css")
    expected_mtime = int(os.stat(style_path).st_mtime)

    assert _static_url("style.css") == f"/static/style.css?v={expected_mtime}"


def test_reload_events_disabled_without_dev_mode(client):
    response = client.get("/dev/reload-events", auth=None)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_reload_events_available_in_dev_mode():
    from app.dev_reload import BOOT_ID, reload_events

    response = await reload_events()

    assert response.media_type == "text/event-stream"
    assert response.headers["Cache-Control"] == "no-cache"

    first_chunk = await anext(response.body_iterator)
    assert BOOT_ID in first_chunk
