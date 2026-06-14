"""Test Stash CLI commands."""

from __future__ import annotations

import json


def test_help(runner, cli_app) -> None:
    """Root help mentions Stash."""
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0
    assert "Stash" in result.stdout


def test_version(runner, cli_app) -> None:
    """Version flag prints version and exits."""
    result = runner.invoke(cli_app, ["--version"])
    assert result.exit_code == 0
    assert "stash version" in result.stdout


def test_init_and_entry_lifecycle(runner, cli_app, vault_dir) -> None:
    """Full lifecycle: init, add, list, show, search, remove."""
    init = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    assert init.exit_code == 0
    assert "initialized" in init.stdout.lower()

    add = runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "entry",
            "add",
            "Docker prune",
            "docker system prune -af",
            "--tag",
            "devops",
            "--tag",
            "docker",
            "--url",
            "https://docs.docker.com",
        ],
    )
    assert add.exit_code == 0
    assert "Added entry" in add.stdout

    list_result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "list", "--tag", "devops"],
    )
    assert list_result.exit_code == 0
    assert "Docker prune" in list_result.stdout

    search = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "search", "prune"],
    )
    assert search.exit_code == 0
    assert "Docker prune" in search.stdout

    json_list = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "entry", "list"],
    )
    assert json_list.exit_code == 0
    data = json.loads(json_list.stdout)
    assert len(data) == 1
    entry_id = data[0]["id"]

    show = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "show", entry_id],
    )
    assert show.exit_code == 0
    assert "docker system prune" in show.stdout

    remove = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "remove", entry_id, "--force"],
    )
    assert remove.exit_code == 0
    assert "Removed" in remove.stdout


def test_entry_list_alias(runner, cli_app, vault_dir) -> None:
    """Custom command name 'ls' works for entry list."""
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "ls"],
    )
    assert result.exit_code == 0


def test_tags_commands(runner, cli_app, vault_dir) -> None:
    """Tag list/add/remove commands work."""
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    add = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "tags", "add", "python"],
    )
    assert add.exit_code == 0

    list_tags = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "tags", "list"],
    )
    assert list_tags.exit_code == 0
    assert "python" in list_tags.stdout


def test_config_path(runner, cli_app, vault_dir) -> None:
    """Config path command prints data directory."""
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "config", "path"],
    )
    assert result.exit_code == 0
    assert str(vault_dir) in result.stdout


def test_vault_not_initialized(runner, cli_app, vault_dir) -> None:
    """Commands fail gracefully when vault is missing."""
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "list"],
    )
    assert result.exit_code == 2
    assert "not initialized" in result.stdout.lower()
