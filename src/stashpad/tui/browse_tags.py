"""Tag filter helpers for the browse TUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from stashpad.models import Entry, EntryKind
from stashpad.schemas import EntryFilter

if TYPE_CHECKING:
    from stashpad.storage import VaultStorage

ALL_TAGS = ""
UNTAGGED_FILTER = "__untagged__"


@dataclass(frozen=True)
class TagFilterOption:
    """A tag row shown in the filter sidebar."""

    option_id: str
    label: str
    entry_count: int


def format_tag_filter_label(name: str, entry_count: int, *, selected: bool) -> str:
    """Format a tag filter row with selection marker and count.

    Parameters
    ----------
    name : str
        Display name for the tag or special row.
    entry_count : int
        Number of matching entries.
    selected : bool
        Whether the filter is currently active.

    Returns
    -------
    str
        Label text such as ``[x] devops (3)``.
    """
    marker = "[x]" if selected else "[ ]"
    return f"{marker} {name} ({entry_count})"


def build_tag_filter_options(
    entries: list[Entry],
    *,
    all_label: str = "All entries",
) -> list[TagFilterOption]:
    """Build sidebar tag filter options from a pre-filtered entry set.

    Parameters
    ----------
    entries : list of Entry
        Entries already filtered by CLI flags (pinned, kind, base tags).
    all_label : str
        Label for the catch-all row.

    Returns
    -------
    list of TagFilterOption
        *All* first, tags alphabetically, *Untagged* last when present.
    """
    tag_counts: dict[str, int] = {}
    untagged_count = 0

    for entry in entries:
        if not entry.tags:
            untagged_count += 1
            continue
        for tag in entry.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    options = [
        TagFilterOption(
            option_id=ALL_TAGS,
            label=all_label,
            entry_count=len(entries),
        )
    ]
    options.extend(
        TagFilterOption(
            option_id=tag,
            label=tag,
            entry_count=count,
        )
        for tag, count in sorted(tag_counts.items())
    )
    if untagged_count:
        options.append(
            TagFilterOption(
                option_id=UNTAGGED_FILTER,
                label="Untagged",
                entry_count=untagged_count,
            )
        )
    return options


def load_entries_for_browse_context(
    storage: VaultStorage,
    *,
    base_tags: list[str] | None,
    pinned: bool,
    kind: EntryKind | None,
    limit: int,
) -> list[Entry]:
    """Load entries used to populate tag filters and the entry list.

    Parameters
    ----------
    storage : VaultStorage
        Active vault storage.
    base_tags : list of str, optional
        Tags required by CLI flags before UI filter selection.
    pinned : bool
        Only pinned entries when ``True``.
    kind : EntryKind, optional
        Optional kind filter from CLI flags.
    limit : int
        Maximum entries to load.

    Returns
    -------
    list of Entry
        Entries matching CLI-level filters.
    """
    return storage.list_entries(
        EntryFilter(
            tags=base_tags,
            pinned=True if pinned else None,
            kind=kind,
            limit=limit,
        )
    )


def entry_matches_tag_filters(
    entry: Entry,
    selected_tags: set[str],
    *,
    untagged_only: bool,
) -> bool:
    """Return whether *entry* matches the active tag filter state.

    Multiple selected tags use OR logic — the entry needs at least one of them.
    """
    if untagged_only:
        return not entry.tags
    if not selected_tags:
        return True
    return bool(selected_tags.intersection(entry.tags))


def entries_for_tag_filters(
    entries: list[Entry],
    selected_tags: set[str],
    *,
    untagged_only: bool,
    query: str,
    limit: int,
    exact: bool,
) -> list[Entry]:
    """Filter *entries* by active tag filters, then optionally fuzzy-rank.

    Parameters
    ----------
    entries : list of Entry
        Candidate entries (CLI filters already applied).
    selected_tags : set of str
        Tags where at least one must be present on an entry (OR logic).
    untagged_only : bool
        When ``True``, only entries without tags are returned.
    query : str
        Search text for fuzzy ranking.
    limit : int
        Maximum results after ranking.
    exact : bool
        Disable fuzzy search when ``True``.

    Returns
    -------
    list of Entry
        Entries visible for the current filter selection.
    """
    scoped = [
        entry
        for entry in entries
        if entry_matches_tag_filters(entry, selected_tags, untagged_only=untagged_only)
    ]

    if not query:
        return scoped[:limit]

    from stashpad.search_rank import rank_search_results

    return rank_search_results(scoped, query, limit=limit, fuzzy=not exact)


def initial_selected_tags(base_tags: list[str] | None) -> set[str]:
    """Return tag filters pre-selected from CLI ``--tag`` / ``--tags`` flags."""
    return set(base_tags or [])
