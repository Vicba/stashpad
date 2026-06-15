"""Fuzzy matching and relevance ranking for vault search."""

from __future__ import annotations

from datetime import datetime, timezone

from stash_cli.constants import (
    BOOST_HALF_LIFE_DAYS,
    CONTENT_MATCH_WEIGHT,
    DEFAULT_SEARCH_LIMIT,
    FUZZY_MATCH_DISCOUNT,
    OPENED_BOOST_CAP,
    PRIORITY_BOOST_HIGH,
    PRIORITY_BOOST_LOW,
    PRIORITY_BOOST_MEDIUM,
    RECENCY_BOOST_CAP,
    TAG_MATCH_WEIGHT,
    TITLE_MATCH_WEIGHT,
    URL_MATCH_WEIGHT,
    WORD_PATTERN,
    WORD_TIGHTNESS_BASE,
    WORD_TIGHTNESS_RANGE,
)
from stash_cli.models import Entry, Priority


def rank_search_results(
    entries: list[Entry],
    query: str,
    *,
    limit: int | None = DEFAULT_SEARCH_LIMIT,
    fuzzy: bool = True,
) -> list[Entry]:
    """Return entries matching a query, sorted by relevance.

    Parameters
    ----------
    entries : list of Entry
        Candidate entries to search.
    query : str
        User search string. Multi-word queries require every word to match.
    limit : int, optional
        Maximum number of results to return.
    fuzzy : bool
        When ``True``, allow subsequence fuzzy matches (e.g. ``prn`` → ``prune``).

    Returns
    -------
    list of Entry
        Matching entries, highest relevance first.

    Examples
    --------
    >>> from stash_cli.models import Entry
    >>> docker = Entry(title="Docker prune", content="docker system prune -af")
    >>> rank_search_results([docker], "prn")[0].title
    'Docker prune'
    """
    tokens = parse_query_tokens(query)
    if not tokens:
        return []

    reference_time = datetime.now(timezone.utc)
    ranked = [
        (score, entry)
        for entry in entries
        if (
            score := entry_relevance_score(
                entry, tokens, fuzzy=fuzzy, reference_time=reference_time
            )
        )
        > 0
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)

    results = [entry for _, entry in ranked]
    if limit is not None:
        results = results[:limit]
    return results


def parse_query_tokens(query: str) -> list[str]:
    """Normalize a search query into lowercase tokens.

    Parameters
    ----------
    query : str
        Raw user input.

    Returns
    -------
    list of str
        Non-empty lowercase tokens. Returns an empty list for blank input.

    Examples
    --------
    >>> parse_query_tokens("  Docker Prn  ")
    ['docker', 'prn']
    """
    return [token for token in query.strip().lower().split() if token]


def entry_relevance_score(
    entry: Entry,
    tokens: list[str],
    *,
    fuzzy: bool,
    reference_time: datetime,
) -> float:
    """Compute the total relevance score for one entry.

    The score combines average text-match quality with boosts for priority,
    recent updates, and recent opens.

    Parameters
    ----------
    entry : Entry
        Entry to score.
    tokens : list of str
        Normalized query tokens.
    fuzzy : bool
        Whether fuzzy subsequence matching is enabled.
    reference_time : datetime
        UTC timestamp used for recency calculations.

    Returns
    -------
    float
        Total relevance score, or ``0.0`` when any token fails to match.
    """
    token_scores = [best_token_match_score(entry, token, fuzzy=fuzzy) for token in tokens]
    if any(score <= 0 for score in token_scores):
        return 0.0

    text_score = sum(token_scores) / len(token_scores)
    return (
        text_score
        + priority_boost(entry.priority)
        + decayed_recency_boost(entry.updated_at, RECENCY_BOOST_CAP, reference_time)
        + decayed_recency_boost(entry.opened_at, OPENED_BOOST_CAP, reference_time)
    )


def best_token_match_score(entry: Entry, token: str, *, fuzzy: bool) -> float:
    """Return the best weighted match score for one token.

    Parameters
    ----------
    entry : Entry
        Entry whose fields are searched.
    token : str
        Normalized query token.
    fuzzy : bool
        Whether fuzzy subsequence matching is enabled.

    Returns
    -------
    float
        Highest weighted score across title, content, URL, and tags.
    """
    return max(
        match_text_field(token, text, weight, fuzzy=fuzzy)
        for text, weight in searchable_fields(entry)
    )


def searchable_fields(entry: Entry) -> list[tuple[str, float]]:
    """Return entry text fields and their match weights.

    Parameters
    ----------
    entry : Entry
        Entry to inspect.

    Returns
    -------
    list of tuple[str, float]
        ``(field_text, weight)`` pairs used for ranking.
    """
    fields: list[tuple[str, float]] = [
        (entry.title, TITLE_MATCH_WEIGHT),
        (entry.content, CONTENT_MATCH_WEIGHT),
    ]
    if entry.url:
        fields.append((entry.url, URL_MATCH_WEIGHT))
    fields.extend((tag, TAG_MATCH_WEIGHT) for tag in entry.tags)
    return fields


def match_text_field(token: str, text: str, weight: float, *, fuzzy: bool) -> float:
    """Score how well a token matches one text field.

    Exact substring matches receive the full field weight. Fuzzy matches are
    scaled down using ``FUZZY_MATCH_DISCOUNT``.

    Parameters
    ----------
    token : str
        Normalized query token.
    text : str
        Field text to search.
    weight : float
        Weight applied when the token matches this field.
    fuzzy : bool
        Whether fuzzy subsequence matching is enabled.

    Returns
    -------
    float
        Weighted match score, or ``0.0`` when there is no match.
    """
    lowered_text = text.lower()
    if token in lowered_text:
        return weight

    if not fuzzy:
        return 0.0

    match_ratio = fuzzy_match_ratio(token, lowered_text)
    if match_ratio <= 0:
        return 0.0
    return match_ratio * weight * FUZZY_MATCH_DISCOUNT


def fuzzy_match_ratio(token: str, text: str) -> float:
    """Return the best fuzzy match ratio for a token within text.

    The token may match the full text or any individual word. Word-level
    matches are preferred when the token covers more of the word.

    Parameters
    ----------
    token : str
        Normalized query token.
    text : str
        Lowercased text to search.

    Returns
    -------
    float
        Best match ratio between ``0.0`` and ``1.0``.
    """
    best_ratio = subsequence_match_score(token, text)
    for word in WORD_PATTERN.findall(text):
        word_ratio = subsequence_match_score(token, word)
        if word_ratio <= 0:
            continue
        word_coverage = len(token) / len(word)
        word_ratio *= WORD_TIGHTNESS_BASE + WORD_TIGHTNESS_RANGE * word_coverage
        best_ratio = max(best_ratio, word_ratio)
    return best_ratio


def subsequence_match_score(needle: str, haystack: str) -> float:
    """Score how well *needle* appears in order within *haystack*.

    Parameters
    ----------
    needle : str
        Characters that must appear in order.
    haystack : str
        Text to search.

    Returns
    -------
    float
        Match quality between ``0.0`` and ``1.0``. Returns ``0.0`` when
        *needle* is not a subsequence of *haystack*.

    Examples
    --------
    >>> round(subsequence_match_score("prn", "prune"), 2)
    0.85
    >>> subsequence_match_score("xyz", "prune") == 0.0
    True
    """
    if not needle:
        return 0.0

    matched_positions: list[int] = []
    next_needle_index = 0
    for index, character in enumerate(haystack):
        if next_needle_index < len(needle) and character == needle[next_needle_index]:
            matched_positions.append(index)
            next_needle_index += 1

    if next_needle_index < len(needle):
        return 0.0

    match_span = matched_positions[-1] - matched_positions[0] + 1
    compactness = len(needle) / match_span
    coverage = len(needle) / len(haystack)
    return 0.6 * compactness + 0.4 * min(coverage * 3.0, 1.0)


def priority_boost(priority: Priority) -> float:
    """Return the ranking boost for an entry priority level.

    Parameters
    ----------
    priority : Priority
        Entry priority.

    Returns
    -------
    float
        Boost value added to the text relevance score.

    Examples
    --------
    >>> priority_boost(Priority.HIGH)
    15.0
    """
    if priority == Priority.HIGH:
        return PRIORITY_BOOST_HIGH
    if priority == Priority.MEDIUM:
        return PRIORITY_BOOST_MEDIUM
    return PRIORITY_BOOST_LOW


def decayed_recency_boost(
    timestamp: datetime | None,
    boost_cap: float,
    reference_time: datetime,
) -> float:
    """Return a time-based boost that decays as an entry ages.

    Parameters
    ----------
    timestamp : datetime, optional
        Event time to score, such as ``updated_at`` or ``opened_at``.
    boost_cap : float
        Maximum boost when the event happened at ``reference_time``.
    reference_time : datetime
        UTC "now" used for age calculations.

    Returns
    -------
    float
        Decayed boost value, or ``0.0`` when ``timestamp`` is ``None``.
    """
    if timestamp is None:
        return 0.0

    aware_timestamp = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    age_days = max((reference_time - aware_timestamp).total_seconds() / 86_400, 0.0)
    return float(boost_cap * (0.5 ** (age_days / BOOST_HALF_LIFE_DAYS)))
