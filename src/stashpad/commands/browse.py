"""``stash browse`` — split-pane TUI for exploring vault entries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import typer
from pydantic import ValidationError as PydanticValidationError

from stashpad.completions import complete_tags
from stashpad.constants import DEFAULT_PICK_LIMIT
from stashpad.context import get_ctx
from stashpad.entry_query import combine_tag_filters
from stashpad.exceptions import StashError, ValidationError
from stashpad.models import EntryKind

if TYPE_CHECKING:
    from collections.abc import Callable

    from stashpad.storage import VaultStorage
    from stashpad.tui.browse_app import BrowseOptions

TUI_INSTALL_HINT = "TUI not installed. Run: poetry install -E tui"


def _load_browse_app() -> tuple[type[BrowseOptions], Callable[[VaultStorage, BrowseOptions], None]]:
    """Import the Textual browse app (optional dependency)."""
    from stashpad.tui.browse_app import BrowseOptions, run_browse_app

    return BrowseOptions, run_browse_app


def browse(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Initial search filter"),
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
    force: bool = typer.Option(False, "--force", "-F", help="Skip run confirmation"),
    first_line: bool = typer.Option(
        False,
        "--first-line",
        "-1",
        help="Copy or run only the first non-empty line",
    ),
) -> None:
    """Browse vault entries in a split-pane terminal UI with toggleable tag filters.

    Requires the optional TUI extra: ``poetry install -E tui``.

    Keyboard shortcuts
    ------------------
    ``t`` tag filters · ``Space``/``Enter`` toggle tag · ``l`` entries · ``/`` search
    ``c`` copy · ``o`` open · ``r`` run · ``d`` delete · ``q`` quit

    Examples
    --------
    $ stash browse
    $ stash browse deploy --tag devops
    $ poetry install -E tui && stash browse --pinned
    """
    app_ctx = get_ctx(ctx)
    if app_ctx.json_output:
        typer.echo("--json is not supported with browse", err=True)
        raise typer.Exit(code=1)

    try:
        browse_options_cls, run_browse_app = _load_browse_app()
    except ImportError:
        typer.echo(TUI_INSTALL_HINT, err=True)
        raise typer.Exit(code=1) from None

    options = browse_options_cls(
        query=query or "",
        tags=combine_tag_filters(tags, tag),
        pinned=pinned,
        kind=kind,
        limit=limit,
        exact=exact,
        force=force,
        first_line_only=first_line,
    )

    try:
        run_browse_app(app_ctx.storage, options)
    except (StashError, PydanticValidationError) as exc:
        message = exc.message if isinstance(exc, StashError) else str(exc)
        typer.echo(message, err=True)
        code = exc.exit_code if isinstance(exc, StashError) else ValidationError.exit_code
        raise typer.Exit(code=code) from exc
