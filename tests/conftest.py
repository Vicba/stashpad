"""Pytest fixtures for Stash CLI tests."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from stash_cli.cli import app


@pytest.fixture()
def runner() -> CliRunner:
    """Return a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture()
def cli_app():
    """Return the Stash Typer application."""
    return app


@pytest.fixture()
def vault_dir(tmp_path, monkeypatch):
    """Provide an isolated vault directory via STASH_DATA_DIR."""
    data_dir = tmp_path / "stash"
    monkeypatch.setenv("STASH_DATA_DIR", str(data_dir))
    return data_dir
