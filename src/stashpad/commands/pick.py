"""``stash pick`` — interactive entry picker (fzf or numbered fallback).

Flow:

1. Load and optionally fuzzy-filter vault entries
2. Let the user pick one row (``fzf`` when installed)
3. Copy, run, or open the selection via ``entry_actions``
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, Optional

import typer
from pydantic import ValidationError as PydanticValidationError

from stashpad.clipboard import copy_to_clipboard
from stashpad.completions import complete_tags
from stashpad.constants import DEFAULT_PICK_LIMIT
from stashpad.context import get_ctx
from stashpad.entry_actions import (
    execute_entry_command,
    get_clipboard_text,
    open_entry_in_browser,
)
from stashpad.exceptions import StashError, ValidationError
from stashpad.models import Entry, EntryKind
from stashpad.output import emit_json, entry_summary
from stashpad.schemas import EntryFilter
from stashpad.search_rank import rank_search_results

if TYPE_CHECKING:
    from stashpad.storage import VaultStorage

EntryPickerFn = Callable[[list[Entry], str], Entry | None]
PickAction = Literal["copy", "run", "open"]


def pick(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Initial search filter"),
    copy: bool = typer.Option(False, "--copy", help="Copy the selected entry"),
    run: bool = typer.Option(False, "--run", help="Run the selected command entry"),
    open_browser: bool = typer.Option(False, "--open", help="Open the selected URL entry"),
    first_line: bool = typer.Option(
        False,
        "--first-line",
        "-1",
        help="Copy or run only the first non-empty line",
    ),
    force: bool = typer.Option(False, "--force", "-F", help="Skip run confirmation"),
    pinned: bool = typer.Option(False, "--pinned", help="Only pinned entries"),
    kind: Optional[EntryKind] = typer.Option(None, "--kind", help="Filter by entry kind"),
    tag: Optional[list[str]] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Filter by tag (repeatable)",
        autocompletion=complete_tags,
    ),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    limit: int = typer.Option(DEFAULT_PICK_LIMIT, "--limit", "-l", min=1),
    exact: bool = typer.Option(False, "--exact", help="Disable fuzzy matching"),
) -> None:
    """Pick an entry from a searchable list, then copy, run, or open it.

    Uses ``fzf`` when installed. Default action is ``--copy``.

    Examples
    --------
    $ stash pick
    $ stash pick deploy --copy
    $ alias sp='stash pick --copy'
    """
    app_ctx = get_ctx(ctx)
    action = _pick_action_from_flags(copy=copy, run=run, open_browser=open_browser)

    try:
        # Step 1: load candidates (storage filter + optional fuzzy rank).
        entries = _load_entries_for_pick(
            app_ctx.storage,
            query=query or "",
            tags=_combine_tag_filters(tags, tag),
            pinned=pinned,
            kind=kind,
            limit=limit,
            exact=exact,
        )

        if app_ctx.json_output:
            emit_json([entry_summary(entry) for entry in entries])
            return
        if not entries:
            typer.echo("No entries to pick.")
            raise typer.Exit

        # Step 2: interactive selection (fzf or numbered list).
        selected = prompt_user_to_pick_entry(entries, query or "")
        if selected is None:
            typer.echo("Cancelled.")
            raise typer.Exit

        # Step 3: bump last-opened timestamp, then copy/run/open.
        entry = app_ctx.storage.touch_entry(selected.id)
        _execute_pick_action(entry, action, first_line_only=first_line, force=force)
    except (StashError, PydanticValidationError) as exc:
        message = exc.message if isinstance(exc, StashError) else str(exc)
        typer.echo(message, err=True)
        code = exc.exit_code if isinstance(exc, StashError) else ValidationError.exit_code
        raise typer.Exit(code=code) from exc


def prompt_user_to_pick_entry(
    entries: list[Entry],
    query: str = "",
    *,
    picker: EntryPickerFn | None = None,
) -> Entry | None:
    """Interactively select one entry via ``fzf`` or a numbered list.

    Parameters
    ----------
    entries : list of Entry
        Candidate entries (already filtered and ranked).
    query : str
        Initial filter string passed through to ``fzf``.
    picker : callable, optional
        Injectable picker for tests; receives ``(entries, query)``.

    Returns
    -------
    Entry or None
        Selected entry, or ``None`` when the user cancels.
    """
    if not entries:
        return None
    return (picker or _prompt_with_fzf_or_numbered_list)(entries, query)


def _pick_action_from_flags(*, copy: bool, run: bool, open_browser: bool) -> PickAction:
    """Map CLI flags to a single pick action. Default is ``copy``."""
    flags = (copy, run, open_browser)
    if sum(flags) > 1:
        raise typer.BadParameter("Use only one of --copy, --run, or --open")
    if run:
        return "run"
    if open_browser:
        return "open"
    return "copy"


def _combine_tag_filters(tags: str | None, tag: list[str] | None) -> list[str] | None:
    """Merge ``--tags`` and repeated ``--tag`` values into one filter list."""
    combined: list[str] = []
    if tags:
        combined.extend(part.strip() for part in tags.split(",") if part.strip())
    if tag:
        combined.extend(tag)
    return combined or None


def _load_entries_for_pick(
    storage: VaultStorage,
    *,
    query: str,
    tags: list[str] | None,
    pinned: bool,
    kind: EntryKind | None,
    limit: int,
    exact: bool,
) -> list[Entry]:
    """List vault entries for the picker, then fuzzy-rank by *query*."""
    entries = storage.list_entries(
        EntryFilter(
            tags=tags,
            pinned=True if pinned else None,
            kind=kind,
            limit=limit,
        )
    )
    # No query: show storage order. With query: re-rank by fuzzy match score.
    if not query:
        return entries
    return rank_search_results(entries, query, limit=limit, fuzzy=not exact)


def _execute_pick_action(
    entry: Entry,
    action: PickAction,
    *,
    first_line_only: bool,
    force: bool,
) -> None:
    """Run the chosen action on the picked entry."""
    if action == "copy":
        copy_to_clipboard(get_clipboard_text(entry, first_line_only=first_line_only))
        typer.echo(f"Copied from '{entry.title}' to clipboard")
        return

    if action == "run":
        exit_code = execute_entry_command(entry, first_line_only=first_line_only, force=force)
        if exit_code != 0:
            typer.echo(f"Command exited with code {exit_code}", err=True)
        # Propagate subprocess exit code to the shell (e.g. for alias wrappers).
        raise typer.Exit(code=exit_code)

    opened = open_entry_in_browser(entry)
    typer.echo(f"Opened {opened}")


def _format_entry_pick_label(entry: Entry) -> str:
    """Single-line label shown in the fzf / numbered picker."""
    tags = ", ".join(entry.tags) if entry.tags else "-"
    return f"[{entry.kind.value}] {entry.title}  {tags}  {str(entry.id)[:8]}"


def _prompt_with_fzf_or_numbered_list(entries: list[Entry], query: str) -> Entry | None:
    """Try ``fzf`` first; fall back to a numbered terminal list."""
    if shutil.which("fzf"):
        selected = _prompt_with_fzf(entries, query)
        if selected is not None:
            return selected
    return _prompt_with_numbered_list(entries, query)


def _prompt_with_fzf(entries: list[Entry], query: str) -> Entry | None:
    """Launch ``fzf`` with tab-separated id + label rows."""
    # id is column 1 (hidden from display); label is column 2+.
    lines = [f"{entry.id}\t{_format_entry_pick_label(entry)}" for entry in entries]
    command = [
        "fzf",
        "--delimiter",
        "\t",
        "--with-nth",
        "2..",  # show only the human-readable label
        "--prompt",
        "stash> ",
        "--height",
        "40%",
        "--reverse",
    ]
    if query:
        command.extend(["--query", query])

    try:
        completed = subprocess.run(
            command,
            input="\n".join(lines),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    # returncode 130 = user pressed Ctrl-C in fzf.
    if completed.returncode != 0:
        return None

    # stdout is "uuid\tlabel"; we only need the id to map back to Entry.
    selected_id = completed.stdout.strip().split("\t", maxsplit=1)[0]
    return next((entry for entry in entries if str(entry.id) == selected_id), None)


def _prompt_with_numbered_list(entries: list[Entry], query: str) -> Entry | None:
    """Show up to 50 numbered rows when ``fzf`` is not available."""
    if query:
        # Fallback has no live search — pre-filter before showing the list.
        entries = rank_search_results(entries, query, limit=len(entries), fuzzy=True)
    if not entries:
        typer.echo("No matching entries.")
        return None

    typer.echo("Pick an entry (install fzf for a searchable picker):")
    visible = entries[:50]  # keep the prompt readable in small terminals
    for index, entry in enumerate(visible, start=1):
        typer.echo(f"  {index:2}. {_format_entry_pick_label(entry)}")

    choice = typer.prompt("Number (empty to cancel)", default="", show_default=False)
    if not choice.strip():
        return None
    try:
        selected = int(choice)
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid selection '{choice}'") from exc
    if selected < 1 or selected > len(visible):
        raise typer.BadParameter(f"Selection out of range: {selected}")
    return visible[selected - 1]
