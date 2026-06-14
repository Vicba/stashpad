"""Custom Typer parameter validators backed by Pydantic.

Typer chapter: Custom Types — https://typer.tiangolo.com/tutorial/parameter-types/custom-types/
"""

from __future__ import annotations

from typing import Optional

import typer
from pydantic import ValidationError as PydanticValidationError

from stash_cli.schemas import EntryCreate


def validate_url(value: Optional[str]) -> Optional[str]:
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
        return validated.url
    except PydanticValidationError as exc:
        raise typer.BadParameter(str(exc.errors()[0]["msg"])) from exc


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
        raise typer.BadParameter("Value must not be empty")
    return value.strip()
