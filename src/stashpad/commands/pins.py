"""List pinned vault entries."""

from __future__ import annotations

import typer
from pydantic import ValidationError as PydanticValidationError

from stashpad.constants import DEFAULT_PINS_LIMIT
from stashpad.context import get_ctx
from stashpad.exceptions import StashError, ValidationError
from stashpad.models import SortOrder
from stashpad.output import render_entry_list
from stashpad.schemas import EntryFilter


def list_pins(
    ctx: typer.Context,
    limit: int = typer.Option(DEFAULT_PINS_LIMIT, "--limit", "-l", min=1),
    sort: SortOrder = typer.Option(SortOrder.TITLE, "--sort", help="Sort order"),
) -> None:
    """List pinned entries — your daily go-to commands and links.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    limit : int
        Maximum number of pinned entries to show.
    sort : SortOrder
        Sort order for results.

    Returns
    -------
    None

    Examples
    --------
    $ stash pins
    $ stash pins --limit 20 --sort newest
    """
    app_ctx = get_ctx(ctx)
    try:
        filters = EntryFilter(pinned=True, limit=limit, sort=sort)
        entries = app_ctx.storage.list_entries(filters)
        render_entry_list(
            entries,
            json_output=app_ctx.json_output,
            title="Pinned",
            empty_message="No pinned entries. Pin one with: stash entry pin <id>",
        )
    except (StashError, PydanticValidationError) as exc:
        message = exc.message if isinstance(exc, StashError) else str(exc)
        typer.echo(message, err=True)
        code = exc.exit_code if isinstance(exc, StashError) else ValidationError.exit_code
        raise typer.Exit(code=code) from exc
