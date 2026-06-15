"""Entry actions: copy, run, and open with kind-aware guards.

Each action checks the entry kind (or infers it for legacy vault data) before
running:

- ``get_clipboard_text`` — copy URL or body to the clipboard
- ``execute_entry_command`` — shell exec; ``command`` entries only
- ``open_entry_in_browser`` — browser open; ``url`` entries only
"""

from __future__ import annotations

import subprocess
import webbrowser

import typer

from stashpad.exceptions import ValidationError
from stashpad.kind import detect_entry_kind
from stashpad.models import Entry, EntryKind


def resolve_entry_kind(entry: Entry) -> EntryKind:
    """Return the kind that governs copy/run/open for *entry*.

    Uses the stored ``entry.kind`` when set. Entries saved before the ``kind``
    field existed are stored as ``note``; for those, kind is re-detected from
    content and URL so old commands and bookmarks keep working.

    Parameters
    ----------
    entry : Entry
        Vault entry.

    Returns
    -------
    EntryKind
        Resolved kind for action checks.
    """
    if entry.kind != EntryKind.NOTE:
        return entry.kind
    # Pre-kind vault entries default to NOTE; re-detect so old commands still run.
    return detect_entry_kind(content=entry.content, url=entry.url)


def get_entry_body_text(entry: Entry, *, first_line_only: bool = False) -> str:
    """Return entry body text, optionally limited to the first non-empty line.

    Parameters
    ----------
    entry : Entry
        Vault entry.
    first_line_only : bool
        When ``True``, return only the first non-empty line (typical command).

    Returns
    -------
    str
        Content to copy or execute.
    """
    if not first_line_only:
        return entry.content
    # Skip blank lines — commands often have a title line above the actual command.
    for line in entry.content.splitlines():
        if stripped := line.strip():
            return stripped
    return entry.content.strip()


def get_clipboard_text(entry: Entry, *, first_line_only: bool = False) -> str:
    """Return the string that should be copied to the clipboard.

    URL entries copy ``entry.url``; all other kinds copy body text.

    Parameters
    ----------
    entry : Entry
        Vault entry.
    first_line_only : bool
        When ``True``, copy only the first non-empty body line.

    Returns
    -------
    str
        Clipboard payload.

    Raises
    ------
    ValidationError
        If there is nothing to copy.
    """
    kind = resolve_entry_kind(entry)
    # URL bookmarks copy the link, not optional notes in the body.
    if kind == EntryKind.URL:
        if not entry.url:
            raise ValidationError(f"Entry '{entry.id}' has no URL to copy")
        return entry.url

    text = get_entry_body_text(entry, first_line_only=first_line_only)
    if not text:
        raise ValidationError(f"Entry '{entry.id}' has no content to copy")
    return text


def execute_entry_command(
    entry: Entry,
    *,
    first_line_only: bool = False,
    force: bool = False,
) -> int:
    """Execute a ``command`` entry in the user's shell.

    Parameters
    ----------
    entry : Entry
        Vault entry.
    first_line_only : bool
        Run only the first non-empty line when ``True``.
    force : bool
        Skip the confirmation prompt when ``True``.

    Returns
    -------
    int
        Subprocess exit code.

    Raises
    ------
    ValidationError
        If the entry is not a command or has no runnable text.
    typer.Exit
        When the user declines confirmation.
    """
    if resolve_entry_kind(entry) != EntryKind.COMMAND:
        raise ValidationError(
            f"Entry '{entry.id}' is a {entry.kind.value}, not a command. "
            "Use `stash entry edit --kind command` to fix it."
        )

    command = get_entry_body_text(entry, first_line_only=first_line_only)
    if not command:
        raise ValidationError(f"Entry '{entry.id}' has no content to run")
    if not force and not typer.confirm(f"Run: {command}?"):
        typer.echo("Cancelled.")
        raise typer.Exit

    # shell=True so pipes, redirects, and env vars work as the user typed them.
    result = subprocess.run(command, shell=True, check=False)  # noqa: S602
    return result.returncode


def open_entry_in_browser(entry: Entry) -> str:
    """Open a ``url`` entry in the default system browser.

    Parameters
    ----------
    entry : Entry
        Vault entry.

    Returns
    -------
    str
        URL that was opened.

    Raises
    ------
    ValidationError
        If the entry is not a URL bookmark or has no URL field.
    """
    if resolve_entry_kind(entry) != EntryKind.URL:
        raise ValidationError(
            f"Entry '{entry.id}' is a {entry.kind.value}, not a URL. "
            "Use `stash open` only on url entries."
        )
    if not entry.url:
        raise ValidationError(f"Entry '{entry.id}' has no URL")

    webbrowser.open(entry.url)
    return entry.url
