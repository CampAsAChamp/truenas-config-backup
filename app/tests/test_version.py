from src.version import get_display_version, get_version


def test_get_display_version_production():
    assert get_display_version(dev_mode=False) == f"v{get_version()}"


def test_get_display_version_dev_mode():
    assert get_display_version(dev_mode=True) == f"Local ({get_version()})"
