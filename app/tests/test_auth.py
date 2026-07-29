from src import config
from src.auth import session_cookie_value, verify_session


def test_session_cookie_matches_configured_password(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret-one")
    token_one = session_cookie_value()

    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret-two")
    token_two = session_cookie_value()

    assert token_one != token_two
    assert verify_session(token_one) is False
    assert verify_session(token_two) is True


def test_verify_session_rejects_missing_or_invalid_cookie(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret")
    assert verify_session(None) is False
    assert verify_session("") is False
    assert verify_session("not-a-valid-token") is False
