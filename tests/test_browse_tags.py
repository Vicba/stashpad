"""Tests for browse TUI tag filter helpers."""

from __future__ import annotations

from stashpad.models import Entry, EntryKind
from stashpad.tui.browse_tags import (
    ALL_TAGS,
    UNTAGGED_FILTER,
    build_tag_filter_options,
    entries_for_tag_filters,
    entry_matches_tag_filters,
    initial_selected_tags,
)


def _entry(title: str, *, tags: list[str] | None = None) -> Entry:
    return Entry(title=title, content=title, tags=tags or [], kind=EntryKind.NOTE)


def test_build_tag_filter_options_counts_tags_and_untagged() -> None:
    entries = [
        _entry("A", tags=["devops", "docker"]),
        _entry("B", tags=["devops"]),
        _entry("C"),
    ]
    options = build_tag_filter_options(entries)
    by_id = {option.option_id: option.entry_count for option in options}

    assert by_id[ALL_TAGS] == 3
    assert by_id["devops"] == 2
    assert by_id["docker"] == 1
    assert by_id[UNTAGGED_FILTER] == 1


def test_entries_for_tag_filters_single_tag() -> None:
    entries = [
        _entry("A", tags=["devops"]),
        _entry("B", tags=["python"]),
        _entry("C"),
    ]
    scoped = entries_for_tag_filters(
        entries,
        {"devops"},
        untagged_only=False,
        query="",
        limit=10,
        exact=False,
    )
    assert [entry.title for entry in scoped] == ["A"]


def test_entries_for_tag_filters_multiple_tags_or_logic() -> None:
    entries = [
        _entry("A", tags=["devops", "k8s"]),
        _entry("B", tags=["devops"]),
        _entry("C", tags=["k8s"]),
        _entry("D", tags=["python"]),
    ]
    scoped = entries_for_tag_filters(
        entries,
        {"devops", "k8s"},
        untagged_only=False,
        query="",
        limit=10,
        exact=False,
    )
    assert {entry.title for entry in scoped} == {"A", "B", "C"}


def test_entries_for_tag_filters_untagged() -> None:
    entries = [_entry("A", tags=["devops"]), _entry("B")]
    scoped = entries_for_tag_filters(
        entries,
        set(),
        untagged_only=True,
        query="",
        limit=10,
        exact=False,
    )
    assert [entry.title for entry in scoped] == ["B"]


def test_entry_matches_tag_filters_uses_or_logic() -> None:
    entry = _entry("A", tags=["devops", "k8s"])
    assert entry_matches_tag_filters(entry, {"devops"}, untagged_only=False)
    assert entry_matches_tag_filters(entry, {"k8s"}, untagged_only=False)
    assert entry_matches_tag_filters(entry, {"devops", "python"}, untagged_only=False)
    assert not entry_matches_tag_filters(entry, {"python"}, untagged_only=False)


def test_initial_selected_tags_from_cli() -> None:
    assert initial_selected_tags(["devops", "k8s"]) == {"devops", "k8s"}
    assert initial_selected_tags(None) == set()
