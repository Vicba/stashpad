"""Tests for fuzzy search ranking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from stashpad.models import Entry, Priority
from stashpad.search_rank import (
    parse_query_tokens,
    rank_search_results,
    subsequence_match_score,
)


def _make_entry(
    title: str,
    content: str = "",
    *,
    priority: Priority = Priority.MEDIUM,
    updated_at: datetime | None = None,
    opened_at: datetime | None = None,
) -> Entry:
    """Build a test entry with optional timestamps."""
    now = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
    return Entry(
        title=title,
        content=content,
        priority=priority,
        updated_at=updated_at or now,
        opened_at=opened_at,
    )


def test_parse_query_tokens_normalizes_input() -> None:
    """Query tokens are lowercased and trimmed."""
    assert parse_query_tokens("  Docker Prn  ") == ["docker", "prn"]


def test_fuzzy_prn_matches_docker_prune() -> None:
    """Abbreviated query matches prune via subsequence fuzzy search."""
    docker = _make_entry("Docker prune", "docker system prune -af")
    results = rank_search_results([docker], "prn")
    assert len(results) == 1
    assert results[0].title == "Docker prune"


def test_exact_mode_requires_substring() -> None:
    """Exact search does not match fuzzy abbreviations."""
    docker = _make_entry("Docker prune", "docker system prune -af")
    assert rank_search_results([docker], "prn", fuzzy=False) == []
    assert len(rank_search_results([docker], "prune", fuzzy=False)) == 1


def test_priority_boost_ranks_higher_first() -> None:
    """High-priority entry ranks above a similar low-priority match."""
    low = _make_entry("Docker prune low", "docker system prune -af", priority=Priority.LOW)
    high = _make_entry("Docker prune high", "docker system prune -af", priority=Priority.HIGH)
    results = rank_search_results([low, high], "docker prune")
    assert results[0].title == "Docker prune high"


def test_opened_boost_ranks_recently_used_first() -> None:
    """Recently opened entry ranks above an otherwise similar entry."""
    now = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
    stale = _make_entry(
        "Docker prune stale",
        "docker system prune -af",
        opened_at=now - timedelta(days=30),
    )
    recent = _make_entry(
        "Docker prune recent",
        "docker system prune -af",
        opened_at=now - timedelta(hours=1),
    )
    results = rank_search_results([stale, recent], "docker prune")
    assert results[0].title == "Docker prune recent"


def test_subsequence_match_score_prn_on_prune() -> None:
    """Subsequence score is positive for prn on prune."""
    assert subsequence_match_score("prn", "prune") > 0.5
