"""Tests for pinned entry support."""

from __future__ import annotations

from stash_cli.models import SortOrder
from stash_cli.schemas import EntryCreate, EntryFilter, EntryUpdate
from stash_cli.storage import VaultStorage


def test_pin_and_list_pinned(tmp_path) -> None:
    """Pinned entries are filterable via EntryFilter."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    pinned = storage.add_entry(EntryCreate(title="Deploy", content="kubectl apply -f", pinned=True))
    storage.add_entry(EntryCreate(title="Other", content="echo hi"))

    results = storage.list_entries(EntryFilter(pinned=True))
    assert len(results) == 1
    assert results[0].id == pinned.id


def test_set_pinned_via_update(tmp_path) -> None:
    """Pin and unpin via EntryUpdate."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    entry = storage.add_entry(EntryCreate(title="A", content="body"))

    pinned = storage.update_entry(entry.id, EntryUpdate(pinned=True))
    assert pinned.pinned is True

    reloaded = storage.get_entry(entry.id)
    assert reloaded.pinned is True

    unpinned = storage.update_entry(entry.id, EntryUpdate(pinned=False))
    assert unpinned.pinned is False

    reloaded = storage.get_entry(entry.id)
    assert reloaded.pinned is False


def test_list_pinned_sorted_by_title(tmp_path) -> None:
    """Pinned list can be sorted alphabetically by title."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(EntryCreate(title="Zebra", content="z", pinned=True))
    storage.add_entry(EntryCreate(title="Alpha", content="a", pinned=True))

    results = storage.list_entries(EntryFilter(pinned=True, sort=SortOrder.TITLE))
    assert [entry.title for entry in results] == ["Alpha", "Zebra"]
