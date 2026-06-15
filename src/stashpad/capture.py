"""Resolve entry body text from arguments, stdin, or the clipboard."""

from __future__ import annotations

import sys

from stashpad.clipboard import read_from_clipboard
from stashpad.constants import STDIN_CONTENT_ALIAS
from stashpad.exceptions import ValidationError


def read_from_stdin() -> str:
    """Read piped or redirected stdin as UTF-8 text.

    Returns
    -------
    str
        Full stdin contents.

    Raises
    ------
    ValidationError
        If stdin is a TTY or empty after stripping.

    Examples
    --------
    >>> read_from_stdin()  # doctest: +SKIP
    """
    if sys.stdin.isatty():
        msg = "No stdin available. Pipe content or pass '-' as the content argument."
        raise ValidationError(msg)

    data = sys.stdin.read()
    if not data.strip():
        msg = "stdin is empty"
        raise ValidationError(msg)
    return data


def resolve_entry_content(
    content: str | None,
    *,
    from_stdin: bool = False,
    from_clipboard: bool = False,
) -> str:
    """Choose entry body text from a positional value, stdin, or clipboard.

    Parameters
    ----------
    content : str, optional
        Positional content argument. Use ``-`` to read from stdin.
    from_stdin : bool
        When ``True``, read body text from stdin.
    from_clipboard : bool
        When ``True``, read body text from the system clipboard.

    Returns
    -------
    str
        Resolved entry body.

    Raises
    ------
    ValidationError
        If both capture flags are set, no source is provided, or stdin is empty.

    Examples
    --------
    >>> resolve_entry_content("docker ps")
    'docker ps'
    """
    if from_stdin and from_clipboard:
        msg = "Use only one of --from-stdin or --clipboard"
        raise ValidationError(msg)

    if from_clipboard:
        return read_from_clipboard()
    if from_stdin or content == STDIN_CONTENT_ALIAS:
        return read_from_stdin()
    if content is None:
        msg = "Content is required unless using --clipboard or --from-stdin"
        raise ValidationError(msg)
    return content
