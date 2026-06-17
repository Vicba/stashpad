"""Tests for stash mcp CLI command."""

from __future__ import annotations

import sys

import pytest

from stashpad.mcp.server import READ_TOOLS, TOOL_ADD, WRITE_TOOLS, list_registered_tool_names


def _init_vault(runner, cli_app, vault_dir) -> None:
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    assert result.exit_code == 0


def test_mcp_serve_rejects_json_output(runner, cli_app, vault_dir) -> None:
    """MCP serve does not support --json."""
    _init_vault(runner, cli_app, vault_dir)
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "mcp", "serve"],
    )
    assert result.exit_code == 1
    assert "--json is not supported" in result.output


def test_mcp_serve_missing_mcp_extra(runner, cli_app, vault_dir, monkeypatch) -> None:
    """Missing MCP SDK shows install hint."""
    import stashpad.commands.mcp as mcp_module

    _init_vault(runner, cli_app, vault_dir)

    def raise_import_error() -> None:
        msg = "mcp not installed"
        raise ImportError(msg)

    monkeypatch.setattr(mcp_module, "_import_mcp_server_runner", raise_import_error)

    result = runner.invoke(cli_app, ["--config-dir", str(vault_dir), "mcp", "serve"])
    assert result.exit_code == 1
    assert "poetry install -E mcp" in result.output


def test_mcp_serve_requires_initialized_vault(runner, cli_app, vault_dir, monkeypatch) -> None:
    """Serve fails when vault is not initialized."""
    pytest.importorskip("mcp")
    import stashpad.commands.mcp as mcp_module

    def fake_run_mcp_server(storage, *, read_only: bool = False) -> None:
        return None

    monkeypatch.setattr(mcp_module, "_import_mcp_server_runner", lambda: fake_run_mcp_server)

    result = runner.invoke(cli_app, ["--config-dir", str(vault_dir), "mcp", "serve"])
    assert result.exit_code == 2
    assert "Vault not initialized" in result.output


def test_mcp_serve_launches_server(runner, cli_app, vault_dir, monkeypatch) -> None:
    """Serve delegates to run_mcp_server with storage and read_only flag."""
    pytest.importorskip("mcp")
    import stashpad.commands.mcp as mcp_module

    _init_vault(runner, cli_app, vault_dir)
    launched: dict[str, object] = {}

    def fake_run_mcp_server(storage, *, read_only: bool = False) -> None:
        launched["storage"] = storage
        launched["read_only"] = read_only

    monkeypatch.setattr(mcp_module, "_import_mcp_server_runner", lambda: fake_run_mcp_server)

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "mcp", "serve", "--read-only"],
    )
    assert result.exit_code == 0
    assert launched["read_only"] is True
    assert launched["storage"].is_initialized is True


@pytest.mark.skipif(
    sys.version_info >= (3, 10), reason="Python version gate only applies below 3.10"
)
def test_mcp_serve_rejects_old_python(runner, cli_app, vault_dir, monkeypatch) -> None:
    """Serve fails on Python versions below 3.10."""
    _init_vault(runner, cli_app, vault_dir)
    result = runner.invoke(cli_app, ["--config-dir", str(vault_dir), "mcp", "serve"])
    assert result.exit_code == 1
    assert "Python 3.10" in result.output


def test_read_only_server_registers_only_read_tools(tmp_path) -> None:
    """Read-only mode omits stash_add from registered tools."""
    pytest.importorskip("mcp")
    from stashpad.mcp.server import build_mcp_server
    from stashpad.mcp.service import VaultMcpService
    from stashpad.schemas import VaultInitOptions
    from stashpad.storage import VaultStorage

    storage = VaultStorage(tmp_path / "vault")
    storage.initialize(VaultInitOptions())

    read_only_server = build_mcp_server(VaultMcpService(storage, read_only=True))
    writable_server = build_mcp_server(VaultMcpService(storage, read_only=False))

    assert list_registered_tool_names(read_only_server) == set(READ_TOOLS)
    assert list_registered_tool_names(writable_server) == set(READ_TOOLS + WRITE_TOOLS)
    assert TOOL_ADD in WRITE_TOOLS
