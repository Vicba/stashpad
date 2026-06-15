"""Open entry URLs in the system browser.

Typer chapter: Launching Applications — https://typer.tiangolo.com/tutorial/launch/
"""

from __future__ import annotations

import webbrowser
from uuid import UUID

import typer

from stash_cli.context import get_ctx
from stash_cli.exceptions import StashError, ValidationError
from stash_cli.output import emit_json


def open_entry(
    ctx: typer.Context,
    entry_id: UUID = typer.Argument(..., help="Entry UUID"),
) -> None:
    """Open the entry URL in your default browser."""
    app_ctx = get_ctx(ctx)
    try:
        entry = app_ctx.storage.touch_entry(entry_id)
        if not entry.url:
            msg = f"Entry '{entry_id}' has no URL"
            raise ValidationError(msg)
        webbrowser.open(entry.url)
        if app_ctx.json_output:
            emit_json({"opened": entry.url, "id": str(entry.id)})
        else:
            typer.echo(f"Opened {entry.url}")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc
