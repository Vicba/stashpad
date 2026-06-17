"""Duplicate detection for vault entries."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any

from stashpad.constants import DUPLICATE_SIMILARITY_THRESHOLD

if TYPE_CHECKING:
    from stashpad.models import Entry
    from stashpad.schemas import EntryCreate


def normalize_field(text: str) -> str:
    """Normalize text for duplicate comparison.

    Parameters
    ----------
    text : str
        Raw field value.

    Returns
    -------
    str
        Lowercased text with collapsed whitespace.

    Examples
    --------
    >>> normalize_field("  Docker   Prune  ")
    'docker prune'
    """
    return " ".join(text.lower().split())


def field_similarity(a: str, b: str) -> float:
    """Return similarity between two field values.

    Parameters
    ----------
    a : str
        First field value.
    b : str
        Second field value.

    Returns
    -------
    float
        Similarity ratio between ``0.0`` and ``1.0``.

    Examples
    --------
    >>> field_similarity("kubectl apply -f", "kubectl apply -f")
    1.0
    """
    normalized_a = normalize_field(a)
    normalized_b = normalize_field(b)
    if not normalized_a and not normalized_b:
        return 1.0
    if normalized_a == normalized_b:
        return 1.0
    return SequenceMatcher(None, normalized_a, normalized_b).ratio()


def _matched_field(title_sim: float, content_sim: float) -> str:
    """Return which field triggered the duplicate match.

    The overall score is ``max(title_sim, content_sim)``. This helper
    identifies whether the match came from title, content, or both fields
    meeting the similarity threshold.

    Parameters
    ----------
    title_sim : float
        Similarity between candidate and existing titles.
    content_sim : float
        Similarity between candidate and existing content.

    Returns
    -------
    str
        ``"title"``, ``"content"``, or ``"both"``.
    """
    if title_sim >= content_sim:
        if (
            content_sim >= DUPLICATE_SIMILARITY_THRESHOLD
            and title_sim >= DUPLICATE_SIMILARITY_THRESHOLD
        ):
            return "both"
        return "title"
    if title_sim >= DUPLICATE_SIMILARITY_THRESHOLD:
        return "both"
    return "content"


@dataclass(frozen=True)
class DuplicateCandidate:
    """A vault entry that is similar to a candidate entry.

    Parameters
    ----------
    entry : Entry
        Existing vault entry.
    score : float
        Similarity score between ``0.0`` and ``1.0``.
    matched_field : str
        Field that triggered the match: ``title``, ``content``, or ``both``.
    """

    entry: Entry
    score: float
    matched_field: str


def entry_similarity(candidate: EntryCreate, existing: Entry) -> tuple[float, str]:
    """Return similarity score and matched field for a candidate vs existing entry.

    Parameters
    ----------
    candidate : EntryCreate
        Proposed entry.
    existing : Entry
        Existing vault entry.

    Returns
    -------
    tuple of (float, str)
        Maximum field similarity and which field matched.
    """
    title_sim = field_similarity(candidate.title, existing.title)
    content_sim = field_similarity(candidate.content, existing.content)
    if title_sim >= content_sim:
        return title_sim, _matched_field(title_sim, content_sim)
    return content_sim, _matched_field(title_sim, content_sim)


def find_duplicate_candidates(
    candidate: EntryCreate,
    entries: list[Entry],
    *,
    threshold: float = DUPLICATE_SIMILARITY_THRESHOLD,
) -> list[DuplicateCandidate]:
    """Find existing entries similar to a candidate.

    Parameters
    ----------
    candidate : EntryCreate
        Proposed entry.
    entries : list of Entry
        Existing entries to compare against.
    threshold : float, optional
        Minimum similarity score to flag as a duplicate.

    Returns
    -------
    list of DuplicateCandidate
        Matching entries sorted by descending similarity score.
    """
    matches: list[DuplicateCandidate] = []
    for entry in entries:
        score, matched_field = entry_similarity(candidate, entry)
        if score >= threshold:
            matches.append(
                DuplicateCandidate(
                    entry=entry,
                    score=score,
                    matched_field=matched_field,
                )
            )
    matches.sort(key=lambda item: item.score, reverse=True)
    return matches


def duplicate_candidate_summary(match: DuplicateCandidate) -> dict[str, Any]:
    """Return a JSON-serializable duplicate candidate summary.

    Parameters
    ----------
    match : DuplicateCandidate
        Duplicate match result.

    Returns
    -------
    dict
        Summary with id, title, score, and matched_field.
    """
    return {
        "id": str(match.entry.id),
        "title": match.entry.title,
        "score": round(match.score, 2),
        "matched_field": match.matched_field,
    }


def format_duplicate_warning(match: DuplicateCandidate) -> str:
    """Format a human-readable duplicate warning line.

    Parameters
    ----------
    match : DuplicateCandidate
        Duplicate match result.

    Returns
    -------
    str
        Warning message for terminal output.
    """
    return f"Warning: similar entry exists: {format_duplicate_match(match)}"


def format_duplicate_match(match: DuplicateCandidate) -> str:
    """Format the match detail portion of a duplicate message.

    Parameters
    ----------
    match : DuplicateCandidate
        Duplicate match result.

    Returns
    -------
    str
        Short id, title, score percent, and matched field.
    """
    short_id = str(match.entry.id)[:8]
    percent = int(round(match.score * 100))
    return f'{short_id} "{match.entry.title}" ({percent}% match, {match.matched_field})'
