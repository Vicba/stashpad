"""Tests for stash browse CLI command and TUI."""

from __future__ import annotations

import asyncio

import pytest


def _init_vault(runner, cli_app, vault_dir) -> None:
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    assert result.exit_code == 0


def test_browse_rejects_json_output(runner, cli_app, vault_dir) -> None:
    _init_vault(runner, cli_app, vault_dir)
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "browse"],
    )
    assert result.exit_code == 1
    assert "--json is not supported" in result.output


def test_browse_missing_tui_extra(runner, cli_app, vault_dir, monkeypatch) -> None:
    import stashpad.commands.browse as browse_module

    _init_vault(runner, cli_app, vault_dir)

    def raise_import_error() -> None:
        msg = "textual not installed"
        raise ImportError(msg)

    monkeypatch.setattr(browse_module, "_load_browse_app", raise_import_error)

    result = runner.invoke(cli_app, ["--config-dir", str(vault_dir), "browse"])
    assert result.exit_code == 1
    assert "poetry install -E tui" in result.output


def test_browse_launches_tui(runner, cli_app, vault_dir, monkeypatch) -> None:
    import stashpad.commands.browse as browse_module
    from stashpad.tui.browse_app import BrowseOptions

    _init_vault(runner, cli_app, vault_dir)
    runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "add", "Deploy", "echo hello"],
    )

    launched: dict[str, object] = {}

    def fake_run_browse_app(storage, options) -> None:
        launched["storage"] = storage
        launched["options"] = options

    monkeypatch.setattr(
        browse_module, "_load_browse_app", lambda: (BrowseOptions, fake_run_browse_app)
    )

    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "browse", "deploy", "--pinned"],
    )
    assert result.exit_code == 0
    options = launched["options"]
    assert isinstance(options, BrowseOptions)
    assert options.query == "deploy"
    assert options.pinned is True


async def _browse_tui_lists_entries(tmp_path) -> None:
    from stashpad.schemas import EntryCreate
    from stashpad.storage import VaultStorage
    from stashpad.tui.browse_app import BrowseApp, BrowseOptions

    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(EntryCreate(title="Deploy", content="echo deploy"))

    async with BrowseApp(storage, BrowseOptions()).run_test() as pilot:
        await pilot.pause()
        assert len(pilot.app._entries_by_id) == 1
        entry = next(iter(pilot.app._entries_by_id.values()))
        assert entry.title == "Deploy"


async def _browse_tui_copy_action(tmp_path, monkeypatch) -> None:
    from stashpad.schemas import EntryCreate
    from stashpad.storage import VaultStorage
    from stashpad.tui.browse_app import BrowseApp, BrowseOptions

    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(EntryCreate(title="Deploy", content="echo deploy"))

    copied: list[str] = []
    monkeypatch.setattr(
        "stashpad.tui.browse_app.copy_to_clipboard",
        lambda text: copied.append(text),
    )

    async with BrowseApp(storage, BrowseOptions()).run_test() as pilot:
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()

    assert copied == ["echo deploy"]


async def _browse_tui_tag_filters_entries(tmp_path) -> None:
    from stashpad.schemas import EntryCreate
    from stashpad.storage import VaultStorage
    from stashpad.tui.browse_app import BrowseApp, BrowseOptions, TagFilterItem

    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(
        EntryCreate(title="Deploy", content="kubectl apply", tags=["devops", "k8s"]),
    )
    storage.add_entry(
        EntryCreate(title="Ops", content="helm upgrade", tags=["devops"]),
    )
    storage.add_entry(
        EntryCreate(title="REPL", content="python", tags=["python"]),
    )

    async with BrowseApp(storage, BrowseOptions()).run_test() as pilot:
        await pilot.pause()
        assert len(pilot.app._entries_by_id) == 3

        devops_item = next(
            child
            for child in pilot.app.query_one("#tag_list").children
            if isinstance(child, TagFilterItem) and child.option.option_id == "devops"
        )
        pilot.app._toggle_tag_filter_item(devops_item)
        await pilot.pause()
        assert pilot.app._selected_tags == {"devops"}
        assert len(pilot.app._entries_by_id) == 2

        k8s_item = next(
            child
            for child in pilot.app.query_one("#tag_list").children
            if isinstance(child, TagFilterItem) and child.option.option_id == "k8s"
        )
        pilot.app._toggle_tag_filter_item(k8s_item)
        await pilot.pause()
        assert pilot.app._selected_tags == {"devops", "k8s"}
        assert len(pilot.app._entries_by_id) == 2
        assert {entry.title for entry in pilot.app._entries_by_id.values()} == {
            "Deploy",
            "Ops",
        }


async def _browse_tui_shows_tag_filters(tmp_path) -> None:
    from stashpad.schemas import EntryCreate
    from stashpad.storage import VaultStorage
    from stashpad.tui.browse_app import BrowseApp, BrowseOptions, TagFilterItem

    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(EntryCreate(title="Deploy", content="kubectl apply", tags=["devops"]))

    async with BrowseApp(storage, BrowseOptions()).run_test() as pilot:
        await pilot.pause()
        tag_items = [
            child
            for child in pilot.app.query_one("#tag_list").children
            if isinstance(child, TagFilterItem)
        ]
        assert len(tag_items) >= 2


async def _browse_tui_delete_entry(tmp_path) -> None:
    from stashpad.schemas import EntryCreate
    from stashpad.storage import VaultStorage
    from stashpad.tui.browse_app import BrowseApp, BrowseOptions

    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(EntryCreate(title="Deploy", content="kubectl apply", tags=["devops"]))
    storage.add_entry(EntryCreate(title="REPL", content="python", tags=["python"]))

    async with BrowseApp(storage, BrowseOptions()).run_test() as pilot:
        await pilot.pause()
        assert len(pilot.app._entries_by_id) == 2
        deleted_id = pilot.app._selected_entry().id
        pilot.app._handle_delete_confirmation(True)
        await pilot.pause()
        assert len(pilot.app._entries_by_id) == 1
        assert deleted_id not in pilot.app._entries_by_id
        assert len(storage.require_vault().entries) == 1


def test_browse_tui_shows_tag_filters(tmp_path) -> None:
    pytest.importorskip("textual")
    asyncio.run(_browse_tui_shows_tag_filters(tmp_path))


def test_browse_tui_delete_entry(tmp_path) -> None:
    pytest.importorskip("textual")
    asyncio.run(_browse_tui_delete_entry(tmp_path))


def test_browse_tui_tag_filters_entries(tmp_path) -> None:
    pytest.importorskip("textual")
    asyncio.run(_browse_tui_tag_filters_entries(tmp_path))


def test_browse_tui_lists_entries(tmp_path) -> None:
    pytest.importorskip("textual")
    asyncio.run(_browse_tui_lists_entries(tmp_path))


def test_browse_tui_copy_action(tmp_path, monkeypatch) -> None:
    pytest.importorskip("textual")
    asyncio.run(_browse_tui_copy_action(tmp_path, monkeypatch))
