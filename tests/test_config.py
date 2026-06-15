"""Test Stash configuration."""

from pathlib import Path

from stashpad.config import get_config, get_settings


def test_get_settings() -> None:
    """Settings return expected defaults."""
    settings = get_settings()
    assert settings.app_name == "Stash"
    assert settings.app_version == "0.1.0"
    assert isinstance(settings.debug, bool)


def test_get_settings_custom_dir(tmp_path: Path) -> None:
    """Settings accept a custom data directory."""
    custom = tmp_path / "custom"
    settings = get_settings(data_dir=custom)
    assert settings.data_dir == custom


def test_get_config() -> None:
    """Config dict includes core keys."""
    config = get_config()
    assert isinstance(config, dict)
    assert config["app_name"] == "Stash"
    assert "data_dir" in config
