"""Configuration management for Stash."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir() -> Path:
    """Return the default XDG config directory for Stash.

    Returns
    -------
    Path
        ``~/.config/stash`` or ``$XDG_CONFIG_HOME/stash``.

    Examples
    --------
    >>> default_data_dir().name
    'stash'
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "stash"
    return Path.home() / ".config" / "stash"


class Settings(BaseSettings):
    """Application settings loaded from environment and ``.env`` file.

    Parameters
    ----------
    app_name : str
        Display name for the application.
    app_version : str
        Semantic version string.
    debug : bool
        Enable debug mode.
    data_dir : Path
        Vault storage directory.
    default_format : str
        Default CLI output format.
    editor : str
        Preferred editor command.
    max_entries : int
        Soft limit for vault size.
    api_host : str
        API bind host.
    api_port : int
        API bind port.
    api_reload : bool
        Enable uvicorn reload in dev.

    Examples
    --------
    >>> Settings().app_name
    'Stash'
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="STASH_",
    )

    app_name: str = "Stash"
    app_version: str = "0.1.0"
    debug: bool = False

    data_dir: Path = Field(default_factory=default_data_dir)
    default_format: str = "table"
    editor: str = "vim"
    max_entries: int = Field(default=10_000, ge=1)

    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_reload: bool = False


def get_settings(data_dir: Optional[Path] = None) -> Settings:
    """Get application settings, optionally overriding the data directory.

    Parameters
    ----------
    data_dir : Path, optional
        Force vault directory for this process.

    Returns
    -------
    Settings
        Validated settings instance.

    Examples
    --------
    >>> get_settings(Path("/tmp/vault")).data_dir
    PosixPath('/tmp/vault')
    """
    settings = Settings()
    if data_dir is not None:
        settings.data_dir = data_dir
    return settings


def get_config(data_dir: Optional[Path] = None) -> dict:
    """Get current configuration as a JSON-serializable dictionary.

    Parameters
    ----------
    data_dir : Path, optional
        Override data directory in the returned config.

    Returns
    -------
    dict
        Settings as plain dict.

    Examples
    --------
    >>> "app_name" in get_config()
    True
    """
    settings = get_settings(data_dir)
    return settings.model_dump(mode="json")
