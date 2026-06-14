"""Test vault storage layer."""

from __future__ import annotations

import pytest

from stash_cli.exceptions import EntryNotFoundError, VaultNotInitializedError
from stash_cli.models import Priority
from stash_cli.schemas import EntryCreate, EntryFilter, SearchQuery
from stash_cli.storage import VaultStorage


def test_initialize_and_add_entry(tmp_path) -> None:
    """Storage can initialize vault and add entries via EntryCreate."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    entry = storage.add_entry(
        EntryCreate(
            title="Test",
            content="Body",
            tags=["python"],
            priority=Priority.HIGH,
        ),
    )
    assert entry.title == "Test"
    assert "python" in entry.tags
    assert storage.list_tags() == ["python"]


def test_require_vault_raises(tmp_path) -> None:
    """Uninitialized vault raises VaultNotInitializedError."""
    storage = VaultStorage(tmp_path / "missing")
    with pytest.raises(VaultNotInitializedError):
        storage.require_vault()


def test_remove_entries(tmp_path) -> None:
    """Bulk remove deletes matching entries."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    entry = storage.add_entry(EntryCreate(title="A", content="content"))
    removed = storage.remove_entries([entry.id])
    assert removed == 1
    with pytest.raises(EntryNotFoundError):
        storage.get_entry(entry.id)


def test_search(tmp_path) -> None:
    """Search finds entries by content using SearchQuery."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(EntryCreate(title="Git rebase", content="git rebase -i HEAD~3"))
    results = storage.search(SearchQuery(query="rebase"))
    assert len(results) == 1


def test_list_entries_filter_tags(tmp_path) -> None:
    """List filters by multiple tags via EntryFilter."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(EntryCreate(title="One", content="c", tags=["work", "python"]))
    storage.add_entry(EntryCreate(title="Two", content="c", tags=["work"]))
    results = storage.list_entries(EntryFilter(tags=["work", "python"]))
    assert len(results) == 1
