"""Tag management commands.

Typer chapters:
- Nested SubCommands — https://typer.tiangolo.com/tutorial/subcommands/
- Sub-Typer Callback Override — https://typer.tiangolo.com/tutorial/subcommands/callback-override/
"""

from __future__ import annotations

from typing import Optional

import typer

from stash_cli.context import get_ctx
from stash_cli.exceptions import StashError
from stash_cli.output import emit_json

tags_app = typer.Typer(help="Manage tags", no_args_is_help=True)


@tags_app.callback()
def tags_callback(
    ctx: typer.Context,
    prefix: Optional[str] = typer.Option(
        None,
        "--prefix",
        "-p",
        help="Filter tags by prefix for all tag commands",
    ),
) -> None:
    """Shared options for tag commands."""
    app_ctx = get_ctx(ctx)
    app_ctx.tag_prefix = prefix


@tags_app.command("list")
def list_tags(ctx: typer.Context) -> None:
    """List all known tags."""
    app_ctx = get_ctx(ctx)
    prefix = app_ctx.tag_prefix
    try:
        tags = app_ctx.storage.list_tags(prefix=prefix)
        if app_ctx.json_output:
            emit_json({"tags": tags, "prefix": prefix})
        elif not tags:
            typer.echo("No tags found.")
        else:
            for tag in tags:
                typer.echo(tag)
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@tags_app.command("add")
def add_tag(
    ctx: typer.Context,
    tag: str = typer.Argument(..., help="Tag name to register"),
) -> None:
    """Add a tag to the vault registry."""
    app_ctx = get_ctx(ctx)
    try:
        normalized = app_ctx.storage.add_tag(tag)
        if app_ctx.json_output:
            emit_json({"tag": normalized})
        else:
            typer.echo(f"Tag '{normalized}' added.")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@tags_app.command("remove")
def remove_tag(
    ctx: typer.Context,
    tag: str = typer.Argument(..., help="Tag name to remove from registry"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Remove a tag from the vault registry."""
    app_ctx = get_ctx(ctx)
    if not force and not typer.confirm(f"Remove tag '{tag}' from registry?"):
        typer.echo("Cancelled.")
        raise typer.Exit()
    try:
        app_ctx.storage.remove_tag(tag)
        if app_ctx.json_output:
            emit_json({"removed": tag})
        else:
            typer.echo(f"Tag '{tag}' removed.")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc
