from unittest.mock import patch

from src import config, history
from src.health import readiness_status


def test_readiness_ready_when_dirs_writable_and_no_history(app_dirs):
    status = readiness_status()

    assert status["ready"] is True
    assert status["backup_dir_writable"] is True
    assert status["config_dir_writable"] is True
    assert status["last_backup"] is None
    assert status["truenas_reachable"] is None


def test_readiness_not_ready_after_failed_backup(app_dirs):
    history.append(success=False, message="api down")

    status = readiness_status()

    assert status["ready"] is False
    assert status["last_backup"]["success"] is False


def test_readiness_checks_truenas_when_enabled(app_dirs, monkeypatch):
    monkeypatch.setattr(config, "HEALTH_CHECK_TRUENAS", True)
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "test-key")

    with patch("src.health.check_truenas_connection") as mock_check:
        status = readiness_status()

    mock_check.assert_called_once()
    assert status["truenas_reachable"] is True
    assert status["ready"] is True


def test_readiness_marks_not_ready_when_truenas_unreachable(app_dirs, monkeypatch):
    monkeypatch.setattr(config, "HEALTH_CHECK_TRUENAS", True)

    with patch("src.health.check_truenas_connection", side_effect=OSError("down")):
        status = readiness_status()

    assert status["truenas_reachable"] is False
    assert status["ready"] is False
