"""Tests for duplicate detection."""

from __future__ import annotations

from stashpad.constants import DUPLICATE_SIMILARITY_THRESHOLD
from stashpad.duplicates import (
    field_similarity,
    find_duplicate_candidates,
    normalize_field,
)
from stashpad.models import Entry
from stashpad.schemas import EntryCreate


def test_normalize_field_collapses_whitespace() -> None:
    """Normalization lowercases and collapses whitespace."""
    assert normalize_field("  Docker   Prune  ") == "docker prune"


def test_field_similarity_exact_match() -> None:
    """Identical normalized content scores 1.0."""
    assert field_similarity("kubectl apply -f deploy.yaml", "kubectl apply -f deploy.yaml") == 1.0


def test_find_duplicate_candidates_exact_content() -> None:
    """Exact content match is flagged as duplicate."""
    existing = Entry(title="Deploy", content="kubectl apply -f deploy.yaml")
    candidate = EntryCreate(title="K8s deploy", content="kubectl apply -f deploy.yaml")
    matches = find_duplicate_candidates(candidate, [existing])
    assert len(matches) == 1
    assert matches[0].score == 1.0
    assert matches[0].matched_field == "content"


def test_find_duplicate_candidates_near_title() -> None:
    """Very similar titles are flagged as duplicates."""
    existing = Entry(title="Docker cleanup", content="docker system prune -af")
    candidate = EntryCreate(title="Docker clean up", content="something else entirely")
    matches = find_duplicate_candidates(candidate, [existing])
    assert len(matches) == 1
    assert matches[0].score >= DUPLICATE_SIMILARITY_THRESHOLD
    assert matches[0].matched_field == "title"


def test_find_duplicate_candidates_no_match() -> None:
    """Unrelated entries are not flagged."""
    existing = Entry(title="Deploy", content="kubectl apply -f")
    candidate = EntryCreate(title="Git status", content="git status")
    matches = find_duplicate_candidates(candidate, [existing])
    assert matches == []


def test_find_duplicate_candidates_below_threshold() -> None:
    """Similar-but-different entries below threshold are ignored."""
    existing = Entry(title="Alpha", content="alpha command one")
    candidate = EntryCreate(title="Beta", content="beta command two")
    matches = find_duplicate_candidates(candidate, [existing])
    assert matches == []


def test_find_duplicate_candidates_intra_batch() -> None:
    """Second item matches first when both are in the comparison set."""
    first = Entry(title="Deploy", content="kubectl apply -f deploy.yaml")
    candidate = EntryCreate(title="Deploy again", content="kubectl apply -f deploy.yaml")
    matches = find_duplicate_candidates(candidate, [first])
    assert len(matches) == 1
    assert matches[0].entry is first
