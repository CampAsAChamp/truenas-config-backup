"""Client for triggering and downloading a TrueNAS config.save backup.

TrueNAS SCALE 25.04+ removed the synchronous REST config/save endpoint.
config.save is now a job (it streams its tar output through a job pipe), so
producing a downloadable file requires the core.download wrapper: it starts
the job over the JSON-RPC websocket API and hands back a one-time HTTP(S)
download URL (``/_download/{job_id}?auth_token=...``) that can be fetched
with a plain GET — no extra auth header needed, the token is in the URL.
"""
import json
import ssl
from urllib.parse import urlparse, urlunparse

import httpx
from websockets.sync.client import connect as ws_connect

WS_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 300


class TrueNASClientError(RuntimeError):
    pass


def _ws_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse((scheme, parsed.netloc, "/api/current", "", "", ""))


def _ssl_context(verify_ssl: bool) -> ssl.SSLContext | None:
    if verify_ssl:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _call(ws, method: str, params: list, request_id: int) -> dict:
    ws.send(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}))
    while True:
        raw = ws.recv(timeout=WS_TIMEOUT)
        msg = json.loads(raw)
        if msg.get("id") == request_id:
            if "error" in msg and msg["error"] is not None:
                raise TrueNASClientError(f"{method} failed: {msg['error']}")
            return msg.get("result")


def check_truenas_connection(base_url: str, api_key: str, verify_ssl: bool) -> None:
    """Verify TrueNAS is reachable and the API key is valid."""
    if not api_key:
        raise TrueNASClientError("TRUENAS_API_KEY is not set")

    ws_url = _ws_url(base_url)
    ssl_context = _ssl_context(verify_ssl) if ws_url.startswith("wss") else None

    with ws_connect(ws_url, ssl_context=ssl_context, open_timeout=WS_TIMEOUT) as ws:
        auth_result = _call(
            ws, "auth.login_with_api_key", [api_key], request_id=1,
        )
        if not auth_result:
            raise TrueNASClientError("TrueNAS API key authentication failed")


def fetch_config_backup(
    base_url: str,
    api_key: str,
    verify_ssl: bool,
    include_secret_seed: bool,
) -> bytes:
    """Trigger config.save via core.download and return the tar bytes."""
    ws_url = _ws_url(base_url)
    ssl_context = _ssl_context(verify_ssl) if ws_url.startswith("wss") else None

    with ws_connect(ws_url, ssl_context=ssl_context, open_timeout=WS_TIMEOUT) as ws:
        auth_result = _call(
            ws, "auth.login_with_api_key", [api_key], request_id=1,
        )
        if not auth_result:
            raise TrueNASClientError("TrueNAS API key authentication failed")

        job_id, download_path = _call(
            ws,
            "core.download",
            [
                "config.save",
                [{"secretseed": include_secret_seed, "root_authorized_keys": False, "pool_keys": False}],
                "freenas-v1.db.tar",
            ],
            request_id=2,
        )

    download_url = f"{base_url}{download_path}"
    with httpx.Client(verify=verify_ssl, timeout=DOWNLOAD_TIMEOUT) as client:
        response = client.get(download_url)
        response.raise_for_status()
        return response.content
