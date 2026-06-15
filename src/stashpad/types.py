"""Custom Typer parameter validators backed by Pydantic.

Typer chapter: Custom Types — https://typer.tiangolo.com/tutorial/parameter-types/custom-types/
"""

from __future__ import annotations

import typer
from pydantic import ValidationError as PydanticValidationError

from stashpad.schemas import EntryCreate


def validate_url(value: str | None) -> str | None:
    """Validate http(s) URLs for CLI options using Pydantic.

    Parameters
    ----------
    value : str, optional
        URL from the CLI option.

    Returns
    -------
    str, optional
        Validated URL, or ``None``.

    Raises
    ------
    typer.BadParameter
        If the URL fails Pydantic validation.

    Examples
    --------
    >>> validate_url("https://example.com")
    'https://example.com'
    >>> validate_url(None) is None
    True
    """
    if value is None:
        return None
    try:
        validated = EntryCreate.model_validate(
            {"title": "_", "content": "_", "url": value},
        )
    except PydanticValidationError as exc:
        raise typer.BadParameter(str(exc.errors()[0]["msg"])) from exc
    else:
        return validated.url


def validate_non_empty(value: str) -> str:
    """Reject blank strings for CLI arguments.

    Parameters
    ----------
    value : str
        Raw CLI string.

    Returns
    -------
    str
        Stripped non-empty string.

    Raises
    ------
    typer.BadParameter
        If the value is blank.

    Examples
    --------
    >>> validate_non_empty("  hello  ")
    'hello'
    """
    if not value or not value.strip():
        msg = "Value must not be empty"
        raise typer.BadParameter(msg)
    return value.strip()
