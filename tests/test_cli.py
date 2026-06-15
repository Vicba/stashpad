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


def _init_and_add_entry(runner, cli_app, vault_dir) -> str:
    """Initialize vault, add one entry, and return its ID."""
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "entry",
            "add",
            "Echo test",
            "echo hello\n# note below",
            "--tag",
            "shell",
        ],
    )
    json_list = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "entry", "list"],
    )
    return json.loads(json_list.stdout)[0]["id"]


def test_entry_copy(runner, cli_app, vault_dir, monkeypatch) -> None:
    """Copy puts entry content on the clipboard."""
    entry_id = _init_and_add_entry(runner, cli_app, vault_dir)
    copied: list[str] = []

    def fake_copy(text: str) -> None:
        copied.append(text)

    monkeypatch.setattr("stash_cli.commands.entry.copy_to_clipboard", fake_copy)

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "copy", entry_id],
    )
    assert result.exit_code == 0
    assert copied == ["echo hello\n# note below"]
    assert "Copied content" in result.stdout

    first_line = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "copy", entry_id, "--first-line"],
    )
    assert first_line.exit_code == 0
    assert copied[-1] == "echo hello"
    assert "Copied first line" in first_line.stdout


def test_entry_copy_json(runner, cli_app, vault_dir, monkeypatch) -> None:
    """Copy with --json returns the copied text."""
    entry_id = _init_and_add_entry(runner, cli_app, vault_dir)
    monkeypatch.setattr("stash_cli.commands.entry.copy_to_clipboard", lambda text: None)

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "entry", "copy", entry_id, "--first-line"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["copied"] == "echo hello"
    assert data["first_line"] is True


def test_entry_run(runner, cli_app, vault_dir, monkeypatch) -> None:
    """Run executes entry content after confirmation."""
    entry_id = _init_and_add_entry(runner, cli_app, vault_dir)
    ran: list[str] = []

    class FakeResult:
        returncode = 0

    def fake_run(command: str, /, **kwargs: object) -> FakeResult:
        ran.append(command)
        return FakeResult()

    monkeypatch.setattr("stash_cli.entry_actions.subprocess.run", fake_run)

    confirmed = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "run", entry_id],
        input="y\n",
    )
    assert confirmed.exit_code == 0
    assert ran == ["echo hello\n# note below"]

    cancelled = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "run", entry_id],
        input="n\n",
    )
    assert cancelled.exit_code == 0
    assert "Cancelled" in cancelled.stdout
    assert len(ran) == 1

    forced = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "run", entry_id, "--first-line", "--force"],
    )
    assert forced.exit_code == 0
    assert ran[-1] == "echo hello"


def _init_vault(runner, cli_app, vault_dir) -> None:
    """Initialize an isolated vault for capture tests."""
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    assert result.exit_code == 0


def test_add_top_level_alias(runner, cli_app, vault_dir) -> None:
    """Top-level 'stash add' mirrors 'stash entry add'."""
    _init_vault(runner, cli_app, vault_dir)
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Quick note", "echo hello"],
    )
    assert result.exit_code == 0
    assert "Added entry" in result.stdout


def test_add_from_stdin_with_dash(runner, cli_app, vault_dir) -> None:
    """Content '-' reads piped stdin into the entry body."""
    _init_vault(runner, cli_app, vault_dir)
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "add", "Recent commits", "-"],
        input="abc123 Fix bug\ndef456 Add tests\n",
    )
    assert result.exit_code == 0
    assert "Added entry 'Recent commits'" in result.stdout

    show = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "entry", "list"],
    )
    entry = json.loads(show.stdout)[0]
    assert "abc123 Fix bug" in entry["content"]


def test_add_from_stdin_flag(runner, cli_app, vault_dir) -> None:
    """--from-stdin reads piped content without passing '-'."""
    _init_vault(runner, cli_app, vault_dir)
    result = runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "add",
            "Piped note",
            "--from-stdin",
        ],
        input="piped body\n",
    )
    assert result.exit_code == 0
    assert "Added entry 'Piped note'" in result.stdout


def test_add_from_clipboard(runner, cli_app, vault_dir, monkeypatch) -> None:
    """--clipboard stores clipboard text as entry content."""
    _init_vault(runner, cli_app, vault_dir)
    monkeypatch.setattr(
        "stash_cli.capture.read_from_clipboard",
        lambda: "clipboard snippet",
    )

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "add", "Snippet", "--clipboard"],
    )
    assert result.exit_code == 0
    assert "Added entry 'Snippet'" in result.stdout


def test_entry_pin_and_pins_command(runner, cli_app, vault_dir) -> None:
    """Pin an entry and list it via stash pins."""
    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Deploy", "kubectl apply -f", "--pin"],
    )
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Other", "echo hi"],
    )

    pins = runner.invoke(cli_app, ["--config-dir", str(vault_dir), "pins"])
    assert pins.exit_code == 0
    assert "Deploy" in pins.stdout
    assert "Other" not in pins.stdout


def test_entry_list_pinned_flag(runner, cli_app, vault_dir) -> None:
    """Entry list --pinned shows only pinned entries."""
    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Daily cmd", "make deploy", "--pin"],
    )

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "list", "--pinned"],
    )
    assert result.exit_code == 0
    assert "Daily cmd" in result.stdout


def test_entry_pin_unpin(runner, cli_app, vault_dir) -> None:
    """Entry pin and unpin toggle the pinned flag."""
    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Toggle me", "cmd"],
    )
    entry_id = json.loads(
        runner.invoke(
            cli_app,
            ["--config-dir", str(vault_dir), "--json", "entry", "list"],
        ).stdout,
    )[0]["id"]

    pin = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "pin", entry_id],
    )
    assert pin.exit_code == 0
    assert "Pinned" in pin.stdout

    pins = runner.invoke(cli_app, ["--config-dir", str(vault_dir), "pins"])
    assert "Toggle me" in pins.stdout

    unpin = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "unpin", entry_id],
    )
    assert unpin.exit_code == 0

    pins_after = runner.invoke(cli_app, ["--config-dir", str(vault_dir), "pins"])
    assert "Toggle me" not in pins_after.stdout
