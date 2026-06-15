"""Open entry URLs in the system browser."""

from __future__ import annotations

from uuid import UUID

import typer

from stashpad.context import get_ctx
from stashpad.entry_actions import open_entry_in_browser
from stashpad.exceptions import StashError
from stashpad.output import emit_json


def open_entry(
    ctx: typer.Context,
    entry_id: UUID = typer.Argument(..., help="Entry UUID"),
) -> None:
    """Open a URL entry in your default browser."""
    app_ctx = get_ctx(ctx)
    try:
        entry = app_ctx.storage.touch_entry(entry_id)
        opened = open_entry_in_browser(entry)
        if app_ctx.json_output:
            emit_json({"opened": opened, "id": str(entry.id)})
        else:
            typer.echo(f"Opened {opened}")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc
