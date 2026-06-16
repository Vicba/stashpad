"""Shared entry loading and labeling for browse and pick flows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from stashpad.models import Entry, EntryKind
from stashpad.schemas import EntryFilter
from stashpad.search_rank import rank_search_results

if TYPE_CHECKING:
    from stashpad.storage import VaultStorage


def combine_tag_filters(tags: str | None, tag: list[str] | None) -> list[str] | None:
    """Merge ``--tags`` and repeated ``--tag`` values into one filter list.

    Parameters
    ----------
    tags : str, optional
        Comma-separated tag string from ``--tags``.
    tag : list of str, optional
        Repeated ``--tag`` values.

    Returns
    -------
    list of str or None
        Combined tag list, or ``None`` when no tags were provided.
    """
    combined: list[str] = []
    if tags:
        combined.extend(part.strip() for part in tags.split(",") if part.strip())
    if tag:
        combined.extend(tag)
    return combined or None


def format_entry_label(entry: Entry) -> str:
    """Single-line label for list rows in pick, browse, and fzf.

    Parameters
    ----------
    entry : Entry
        Vault entry.

    Returns
    -------
    str
        Human-readable row text: ``[kind] title  tags  short_id``.
    """
    tags = ", ".join(entry.tags) if entry.tags else "-"
    return f"[{entry.kind.value}] {entry.title}  {tags}  {str(entry.id)[:8]}"


def load_browsable_entries(
    storage: VaultStorage,
    *,
    query: str,
    tags: list[str] | None,
    pinned: bool,
    kind: EntryKind | None,
    limit: int,
    exact: bool,
) -> list[Entry]:
    """List vault entries for interactive browse/pick, then fuzzy-rank by *query*.

    Parameters
    ----------
    storage : VaultStorage
        Active vault storage.
    query : str
        Search text; when empty, entries keep storage sort order.
    tags : list of str, optional
        Required tags (all must match).
    pinned : bool
        When ``True``, only pinned entries are returned.
    kind : EntryKind, optional
        Filter by entry kind.
    limit : int
        Maximum number of entries.
    exact : bool
        When ``True``, disable fuzzy matching for the query.

    Returns
    -------
    list of Entry
        Filtered and optionally ranked entries.
    """
    entries = storage.list_entries(
        EntryFilter(
            tags=tags,
            pinned=True if pinned else None,
            kind=kind,
            limit=limit,
        )
    )
    if not query:
        return entries
    return rank_search_results(entries, query, limit=limit, fuzzy=not exact)
