"""Shared Pydantic field validators for Stash models."""

from __future__ import annotations

from urllib.parse import urlparse


def normalize_tag_list(tags: list[str]) -> list[str]:
    """Return deduplicated lowercase tags preserving first-seen order.

    Parameters
    ----------
    tags : list of str
        Raw tag strings from user input.

    Returns
    -------
    list of str
        Cleaned, lowercase, deduplicated tags.

    Examples
    --------
    >>> normalize_tag_list(["Python", " CLI ", "python"])
    ['python', 'cli']
    """
    seen: set[str] = set()
    normalized: list[str] = []
    for tag in tags:
        clean = tag.strip().lower()
        if clean and clean not in seen:
            seen.add(clean)
            normalized.append(clean)
    return normalized


def validate_http_url(value: str | None) -> str | None:
    """Validate that a string is a well-formed http(s) URL.

    Parameters
    ----------
    value : str, optional
        URL string to validate.

    Returns
    -------
    str, optional
        The same URL if valid, or ``None``.

    Raises
    ------
    ValueError
        If the URL is not http(s) or missing a host.

    Examples
    --------
    >>> validate_http_url("https://docs.python.org")
    'https://docs.python.org'
    >>> validate_http_url(None) is None
    True
    """
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        msg = f"'{value}' is not a valid http(s) URL"
        raise ValueError(msg)
    return value
