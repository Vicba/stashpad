"""Tests for stash pick and kind CLI behavior."""

from __future__ import annotations

import json

from stashpad.commands.pick import prompt_user_to_pick_entry
from stashpad.models import Entry, EntryKind


def _init_vault(runner, cli_app, vault_dir) -> None:
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    assert result.exit_code == 0


def test_pick_copy_with_injected_picker(runner, cli_app, vault_dir, monkeypatch) -> None:
    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Deploy", "kubectl apply -f"],
    )
    entry_id = json.loads(
        runner.invoke(
            cli_app,
            ["--config-dir", str(vault_dir), "--json", "entry", "list"],
        ).stdout,
    )[0]["id"]

    def fake_picker(entries, query):
        return next(entry for entry in entries if str(entry.id) == entry_id)

    monkeypatch.setattr("stashpad.commands.pick.prompt_user_to_pick_entry", fake_picker)
    monkeypatch.setattr("stashpad.commands.pick.copy_to_clipboard", lambda text: None)

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "pick", "--copy"],
    )
    assert result.exit_code == 0
    assert "Copied from 'Deploy'" in result.stdout


def test_entry_run_rejects_note_kind(runner, cli_app, vault_dir) -> None:
    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "add",
            "Memo",
            "plain note",
            "--kind",
            "note",
        ],
    )
    entry_id = json.loads(
        runner.invoke(
            cli_app,
            ["--config-dir", str(vault_dir), "--json", "entry", "list"],
        ).stdout,
    )[0]["id"]

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "entry", "run", entry_id, "--force"],
    )
    assert result.exit_code != 0
    assert "not a command" in result.output


def test_open_rejects_command_kind(runner, cli_app, vault_dir) -> None:
    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "add",
            "Deploy",
            "kubectl apply -f",
            "--url",
            "https://example.com",
        ],
    )
    entry_id = json.loads(
        runner.invoke(
            cli_app,
            ["--config-dir", str(vault_dir), "--json", "entry", "list"],
        ).stdout,
    )[0]["id"]

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "open", entry_id],
    )
    assert result.exit_code != 0
    assert "not a URL" in result.output


def test_add_infers_command_kind(runner, cli_app, vault_dir) -> None:
    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Deploy", "kubectl apply -f"],
    )
    entry = json.loads(
        runner.invoke(
            cli_app,
            ["--config-dir", str(vault_dir), "--json", "entry", "list"],
        ).stdout,
    )[0]
    assert entry["kind"] == "command"


def test_prompt_user_to_pick_entry_can_cancel() -> None:
    def cancel(_entries, _query):
        return None

    entry = Entry(title="A", content="echo hi", kind=EntryKind.COMMAND)
    assert prompt_user_to_pick_entry([entry], picker=cancel) is None
