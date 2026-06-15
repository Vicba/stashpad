"""Entry CRUD commands.

Typer chapters:
- SubCommands in a Single File — https://typer.tiangolo.com/tutorial/subcommands/single-file/
- Custom Command Name — https://typer.tiangolo.com/tutorial/commands/name/
- Multiple Values — https://typer.tiangolo.com/tutorial/multiple-values/
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Optional
from uuid import UUID

import typer
from pydantic import ValidationError as PydanticValidationError

from stash_cli.capture import resolve_entry_content
from stash_cli.clipboard import copy_to_clipboard
from stash_cli.completions import complete_tags
from stash_cli.constants import DEFAULT_LIST_LIMIT, STDIN_CONTENT_ALIAS
from stash_cli.context import get_ctx
from stash_cli.exceptions import StashError, ValidationError
from stash_cli.models import Entry, Priority, SortOrder
from stash_cli.output import emit_json, entry_summary, print_entry_detail, print_entry_table
from stash_cli.schemas import EntryCreate, EntryFilter, EntryUpdate
from stash_cli.types import validate_url

entry_app = typer.Typer(help="Manage vault entries", no_args_is_help=True)


def _parse_tags(tags: str | None, extra_tags: list[str] | None) -> list[str]:
    """Combine comma-separated tags and repeated ``--tag`` flags.

    Parameters
    ----------
    tags : str, optional
        Comma-separated tag string from ``--tags``.
    extra_tags : list of str, optional
        Values from repeated ``--tag`` options.

    Returns
    -------
    list of str
        Combined raw tag strings (normalization happens in Pydantic).

    Examples
    --------
    >>> _parse_tags("python,cli", ["docker"])
    ['python', 'cli', 'docker']
    """
    combined: list[str] = []
    if tags:
        combined.extend(part.strip() for part in tags.split(",") if part.strip())
    if extra_tags:
        combined.extend(extra_tags)
    return combined


def _entry_command_text(entry: Entry, first_line: bool) -> str:
    """Return full content or only the first non-empty line.

    Parameters
    ----------
    entry : Entry
        Vault entry.
    first_line : bool
        When ``True``, return the first non-empty line only.

    Returns
    -------
    str
        Text to copy or execute.
    """
    if not first_line:
        return entry.content
    for line in entry.content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return entry.content.strip()


def _validate_since(value: str | None) -> datetime | None:
    """Parse ISO date or datetime strings for ``--since`` / ``--until``.

    Parameters
    ----------
    value : str, optional
        Date ``YYYY-MM-DD`` or full ISO datetime.

    Returns
    -------
    datetime, optional
        Parsed datetime, or ``None``.

    Raises
    ------
    typer.BadParameter
        If the string is not valid ISO format.
    """
    if value is None:
        return None
    try:
        if len(value) == 10:
            return datetime.fromisoformat(f"{value}T00:00:00")
        return datetime.fromisoformat(value)
    except ValueError as exc:
        msg = f"Invalid date '{value}'. Use YYYY-MM-DD or ISO datetime."
        raise typer.BadParameter(
            msg
        ) from exc


@entry_app.command("add")
def add_entry(
    ctx: typer.Context,
    title: str = typer.Argument(..., help="Entry title"),
    content: Optional[str] = typer.Argument(
        None,
        help="Entry content, '-' for stdin, or omit with --clipboard / --from-stdin",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
        "-u",
        help="Related URL",
        callback=validate_url,
    ),
    tag: Optional[list[str]] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Tag (repeatable)",
        autocompletion=complete_tags,
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        help="Comma-separated tags (work,python,docker)",
    ),
    priority: Priority = typer.Option(
        Priority.MEDIUM,
        "--priority",
        "-p",
        help="Entry priority",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Prompt for missing fields interactively",
    ),
    from_stdin: bool = typer.Option(
        False,
        "--from-stdin",
        help="Read entry content from stdin (same as passing '-' as content)",
    ),
    from_clipboard: bool = typer.Option(
        False,
        "--clipboard",
        help="Read entry content from the system clipboard",
    ),
) -> None:
    """Add a new entry to the vault.

    Pass ``-`` as the content argument to read from stdin::

        git log --oneline -5 | stash entry add "Recent commits" -

    Parameters
    ----------
    ctx : typer.Context
        Typer context with ``AppContext`` in ``ctx.obj``.
    title : str
        Entry title positional argument.
    content : str
        Entry body, or ``-`` to read from stdin.
    url : str, optional
        Optional http(s) URL.
    tag : list of str, optional
        Repeatable tag option.
    tags : str, optional
        Comma-separated tags.
    priority : Priority
        Entry priority enum.
    interactive : bool
        Prompt for fields when ``True``.
    from_stdin : bool
        Read body from stdin instead of the positional content.
    from_clipboard : bool
        Read body from the system clipboard.

    Returns
    -------
    None

    Examples
    --------
    $ stash entry add "Docker prune" "docker system prune -af" --tag devops
    $ stash entry add "Recent commits" -
    $ stash entry add "Snippet" --clipboard
    $ stash add "Quick note" "echo hello"
    """
    app_ctx = get_ctx(ctx)
    using_capture = from_stdin or from_clipboard or content == STDIN_CONTENT_ALIAS

    if interactive:
        title = typer.prompt("Title", default=title)
        if not using_capture:
            content = typer.prompt("Content", default=content)
        if url is None:
            url_input = typer.prompt("URL (optional)", default="", show_default=False)
            url = url_input or None
        tag_input = typer.prompt("Tags (comma-separated)", default="")
        tags = tag_input or tags

    try:
        content = resolve_entry_content(
            content,
            from_stdin=from_stdin,
            from_clipboard=from_clipboard,
        )
        payload = EntryCreate(
            title=title,
            content=content,
            url=url,
            tags=_parse_tags(tags, tag),
            priority=priority,
        )
        entry = app_ctx.storage.add_entry(payload)
        if app_ctx.json_output:
            emit_json(entry_summary(entry))
        else:
            typer.echo(f"Added entry '{entry.title}' ({entry.id})")
    except (StashError, PydanticValidationError) as exc:
        message = exc.message if isinstance(exc, StashError) else str(exc)
        typer.echo(message, err=True)
        code = exc.exit_code if isinstance(exc, StashError) else ValidationError.exit_code
        raise typer.Exit(code=code) from exc


@entry_app.command("list")
@entry_app.command("ls", hidden=True)
def list_entries(
    ctx: typer.Context,
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        help="Filter by comma-separated tags",
    ),
    tag: Optional[list[str]] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Filter by tag (repeatable)",
        autocompletion=complete_tags,
    ),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p"),
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Show entries created on or after this date",
        callback=_validate_since,
    ),
    until: Optional[str] = typer.Option(
        None,
        "--until",
        help="Show entries created on or before this date",
        callback=_validate_since,
    ),
    limit: int = typer.Option(DEFAULT_LIST_LIMIT, "--limit", "-l", min=1, help="Maximum entries"),
    sort: SortOrder = typer.Option(SortOrder.NEWEST, "--sort", help="Sort order"),
) -> None:
    """List vault entries with optional Pydantic filters.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    tags : str, optional
        Comma-separated required tags.
    tag : list of str, optional
        Repeatable tag filter.
    priority : Priority, optional
        Filter by priority.
    since : str, optional
        Lower date bound (ISO).
    until : str, optional
        Upper date bound (ISO).
    limit : int
        Max results.
    sort : SortOrder
        Sort order enum.

    Returns
    -------
    None

    Examples
    --------
    $ stash entry list --tag devops --limit 10
    $ stash entry ls --tags python,cli
    """
    app_ctx = get_ctx(ctx)
    try:
        parsed_tags = _parse_tags(tags, tag) or None
        filters = EntryFilter(
            tags=parsed_tags,
            priority=priority,
            since=since,
            until=until,
            limit=limit,
            sort=sort,
        )
        entries = app_ctx.storage.list_entries(filters)
        if app_ctx.json_output:
            emit_json([entry_summary(entry) for entry in entries])
        elif not entries:
            typer.echo("No entries found.")
        else:
            print_entry_table(entries)
    except (StashError, PydanticValidationError) as exc:
        message = exc.message if isinstance(exc, StashError) else str(exc)
        typer.echo(message, err=True)
        code = exc.exit_code if isinstance(exc, StashError) else ValidationError.exit_code
        raise typer.Exit(code=code) from exc


@entry_app.command("copy")
def copy_entry(
    ctx: typer.Context,
    entry_id: UUID = typer.Argument(..., help="Entry UUID"),
    first_line: bool = typer.Option(
        False,
        "--first-line",
        "-1",
        help="Copy only the first non-empty line (the command)",
    ),
) -> None:
    """Copy entry content to the system clipboard.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    entry_id : UUID
        Entry identifier.
    first_line : bool
        Copy only the first line when ``True``.

    Returns
    -------
    None

    Examples
    --------
    $ stash entry copy <id>
    $ stash entry copy <id> --first-line
    """
    app_ctx = get_ctx(ctx)
    try:
        entry = app_ctx.storage.touch_entry(entry_id)
        text = _entry_command_text(entry, first_line)
        copy_to_clipboard(text)
        if app_ctx.json_output:
            emit_json({"copied": text, "id": str(entry.id), "first_line": first_line})
        else:
            scope = "first line" if first_line else "content"
            typer.echo(f"Copied {scope} from '{entry.title}' to clipboard")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@entry_app.command("run")
def run_entry(
    ctx: typer.Context,
    entry_id: UUID = typer.Argument(..., help="Entry UUID"),
    first_line: bool = typer.Option(
        False,
        "--first-line",
        "-1",
        help="Run only the first non-empty line (the command)",
    ),
    force: bool = typer.Option(False, "--force", "-F", help="Skip confirmation"),
) -> None:
    """Execute entry content in the shell after confirmation.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    entry_id : UUID
        Entry identifier.
    first_line : bool
        Run only the first line when ``True``.
    force : bool
        Skip confirmation prompt.

    Returns
    -------
    None

    Examples
    --------
    $ stash entry run <id>
    $ stash entry run <id> --first-line --force
    """
    app_ctx = get_ctx(ctx)
    try:
        entry = app_ctx.storage.touch_entry(entry_id)
        command = _entry_command_text(entry, first_line)
        if not command:
            msg = f"Entry '{entry_id}' has no content to run"
            raise ValidationError(msg)

        if not force and not typer.confirm(f"Run: {command}?"):
            typer.echo("Cancelled.")
            raise typer.Exit

        result = subprocess.run(command, shell=True, check=False)  # noqa: S602
        if app_ctx.json_output:
            emit_json(
                {
                    "ran": True,
                    "command": command,
                    "id": str(entry.id),
                    "exit_code": result.returncode,
                }
            )
        elif result.returncode != 0:
            typer.echo(f"Command exited with code {result.returncode}", err=True)
        raise typer.Exit(code=result.returncode)
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@entry_app.command("show")
def show_entry(
    ctx: typer.Context,
    entry_id: UUID = typer.Argument(..., help="Entry UUID"),
) -> None:
    """Show full details for one entry.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    entry_id : UUID
        Entry identifier.

    Returns
    -------
    None

    Examples
    --------
    $ stash entry show 550e8400-e29b-41d4-a716-446655440000
    """
    app_ctx = get_ctx(ctx)
    try:
        entry = app_ctx.storage.touch_entry(entry_id)
        if app_ctx.json_output:
            emit_json(entry_summary(entry))
        else:
            print_entry_detail(entry)
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@entry_app.command("edit")
def edit_entry(
    ctx: typer.Context,
    entry_id: UUID = typer.Argument(..., help="Entry UUID"),
    title: str = typer.Option(..., "--title", help="New title (required)"),
    content: Optional[str] = typer.Option(None, "--content", "-c"),
    url: Optional[str] = typer.Option(None, "--url", "-u", callback=validate_url),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p"),
) -> None:
    """Edit an existing entry using ``EntryUpdate``.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    entry_id : UUID
        Entry to update.
    title : str
        Required new title.
    content : str, optional
        New body content.
    url : str, optional
        New URL.
    tags : str, optional
        Comma-separated replacement tags.
    priority : Priority, optional
        New priority.

    Returns
    -------
    None

    Examples
    --------
    $ stash entry edit <id> --title "New title" --content "updated body"
    """
    app_ctx = get_ctx(ctx)
    try:
        update = EntryUpdate(
            title=title,
            content=content,
            url=url,
            tags=_parse_tags(tags, None) or None,
            priority=priority,
        )
        entry = app_ctx.storage.update_entry(entry_id, update)
        if app_ctx.json_output:
            emit_json(entry_summary(entry))
        else:
            typer.echo(f"Updated entry '{entry.title}'")
    except (StashError, PydanticValidationError) as exc:
        message = exc.message if isinstance(exc, StashError) else str(exc)
        typer.echo(message, err=True)
        code = exc.exit_code if isinstance(exc, StashError) else ValidationError.exit_code
        raise typer.Exit(code=code) from exc


@entry_app.command("remove")
@entry_app.command("rm", hidden=True)
def remove_entries(
    ctx: typer.Context,
    entry_ids: list[UUID] = typer.Argument(..., help="One or more entry UUIDs"),
    force: bool = typer.Option(False, "--force", "-F", help="Skip confirmation"),
) -> None:
    """Remove one or more entries by UUID.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    entry_ids : list of UUID
        One or more entry IDs (multiple values).
    force : bool
        Skip confirmation prompt.

    Returns
    -------
    None

    Examples
    --------
    $ stash entry rm <id1> <id2> --force
    """
    app_ctx = get_ctx(ctx)

    if not force and not typer.confirm(f"Delete {len(entry_ids)} entry/entries?"):
        typer.echo("Cancelled.")
        raise typer.Exit

    try:
        removed = app_ctx.storage.remove_entries(entry_ids)
        if app_ctx.json_output:
            emit_json({"removed": removed, "ids": [str(entry_id) for entry_id in entry_ids]})
        else:
            typer.echo(f"Removed {removed} entry/entries.")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc
