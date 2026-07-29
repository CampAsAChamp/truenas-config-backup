import hashlib
import hmac
import secrets

from fastapi import Request

from . import config

SESSION_COOKIE = "dashboard_session"
SESSION_MAX_AGE = 7 * 24 * 3600
_SESSION_PAYLOAD = b"truenas-config-backup-session"


class AuthRequired(Exception):
    def __init__(self, next_path: str):
        self.next_path = next_path


def _session_token() -> str:
    return hmac.new(
        config.DASHBOARD_PASSWORD.encode("utf-8"),
        _SESSION_PAYLOAD,
        hashlib.sha256,
    ).hexdigest()


def session_cookie_value() -> str:
    return _session_token()


def verify_session(cookie_value: str | None) -> bool:
    if not cookie_value:
        return False
    return secrets.compare_digest(cookie_value, _session_token())


def require_dashboard_auth(request: Request) -> None:
    if verify_session(request.cookies.get(SESSION_COOKIE)):
        return
    raise AuthRequired(request.url.path)
