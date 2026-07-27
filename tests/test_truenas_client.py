import json
import ssl
from unittest.mock import MagicMock, patch

import pytest

from app.truenas_client import (
    TrueNASClientError,
    _ssl_context,
    _ws_url,
    fetch_config_backup,
)


def test_ws_url_http():
    assert _ws_url("http://truenas.local") == "ws://truenas.local/api/current"


def test_ws_url_https():
    assert _ws_url("https://truenas.local") == "wss://truenas.local/api/current"


def test_ssl_context_verify_true():
    assert _ssl_context(True) is None


def test_ssl_context_verify_false():
    ctx = _ssl_context(False)
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.check_hostname is False
    assert ctx.verify_mode == ssl.CERT_NONE


def _mock_ws_messages(auth_ok: bool, download_path: str = "/_download/job-1?auth_token=abc"):
    auth_msg = json.dumps({"jsonrpc": "2.0", "id": 1, "result": auth_ok})
    download_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "result": ["job-1", download_path],
    })
    return [auth_msg, download_msg]


@patch("app.truenas_client.httpx.Client")
@patch("app.truenas_client.ws_connect")
def test_fetch_config_backup_success(mock_ws_connect, mock_client_cls):
    mock_ws = MagicMock()
    mock_ws.recv.side_effect = _mock_ws_messages(auth_ok=True)
    mock_ws_connect.return_value.__enter__.return_value = mock_ws

    mock_response = MagicMock()
    mock_response.content = b"tar-data"
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mock_client_cls.return_value = mock_client

    result = fetch_config_backup(
        base_url="https://truenas.local",
        api_key="test-key",
        verify_ssl=True,
        include_secret_seed=True,
    )

    assert result == b"tar-data"
    mock_ws.send.assert_called()
    mock_client.get.assert_called_once_with("https://truenas.local/_download/job-1?auth_token=abc")


@patch("app.truenas_client.ws_connect")
def test_fetch_config_backup_auth_failure(mock_ws_connect):
    mock_ws = MagicMock()
    mock_ws.recv.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": False})
    mock_ws_connect.return_value.__enter__.return_value = mock_ws

    with pytest.raises(TrueNASClientError, match="authentication failed"):
        fetch_config_backup(
            base_url="https://truenas.local",
            api_key="bad-key",
            verify_ssl=True,
            include_secret_seed=False,
        )


@patch("app.truenas_client.ws_connect")
def test_fetch_config_backup_rpc_error(mock_ws_connect):
    mock_ws = MagicMock()
    mock_ws.recv.return_value = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32600, "message": "invalid"},
    })
    mock_ws_connect.return_value.__enter__.return_value = mock_ws

    with pytest.raises(TrueNASClientError, match="auth.login_with_api_key failed"):
        fetch_config_backup(
            base_url="https://truenas.local",
            api_key="key",
            verify_ssl=True,
            include_secret_seed=True,
        )
