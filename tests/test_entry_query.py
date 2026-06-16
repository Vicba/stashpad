"""Tests for shared entry query helpers."""

from __future__ import annotations

from stashpad.entry_query import combine_tag_filters, format_entry_label, load_browsable_entries
from stashpad.models import Entry, EntryKind
from stashpad.schemas import EntryCreate
from stashpad.storage import VaultStorage


def _storage_with_entries(tmp_path) -> VaultStorage:
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize()
    storage.add_entry(
        EntryCreate(
            title="Docker prune",
            content="docker system prune -f",
            tags=["devops"],
            kind=EntryKind.COMMAND,
        ),
    )
    storage.add_entry(
        EntryCreate(
            title="Docs",
            content="internal wiki",
            url="https://example.com/docs",
            kind=EntryKind.URL,
        ),
    )
    return storage


def test_combine_tag_filters_merges_sources() -> None:
    assert combine_tag_filters("a,b", ["c"]) == ["a", "b", "c"]
    assert combine_tag_filters(None, None) is None


def test_format_entry_label_includes_kind_and_short_id() -> None:
    entry = Entry(title="Deploy", content="kubectl apply", kind=EntryKind.COMMAND)
    label = format_entry_label(entry)
    assert "[command]" in label
    assert "Deploy" in label
    assert str(entry.id)[:8] in label


def test_load_browsable_entries_without_query(tmp_path) -> None:
    storage = _storage_with_entries(tmp_path)
    entries = load_browsable_entries(
        storage,
        query="",
        tags=None,
        pinned=False,
        kind=None,
        limit=100,
        exact=False,
    )
    assert len(entries) == 2


def test_load_browsable_entries_fuzzy_query(tmp_path) -> None:
    storage = _storage_with_entries(tmp_path)
    entries = load_browsable_entries(
        storage,
        query="prn",
        tags=None,
        pinned=False,
        kind=None,
        limit=100,
        exact=False,
    )
    assert len(entries) == 1
    assert entries[0].title == "Docker prune"


def test_load_browsable_entries_kind_filter(tmp_path) -> None:
    storage = _storage_with_entries(tmp_path)
    entries = load_browsable_entries(
        storage,
        query="",
        tags=None,
        pinned=False,
        kind=EntryKind.URL,
        limit=100,
        exact=False,
    )
    assert len(entries) == 1
    assert entries[0].kind == EntryKind.URL
