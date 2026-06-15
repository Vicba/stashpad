"""Configuration commands."""

from __future__ import annotations

import typer

from stashpad.config import get_config
from stashpad.context import get_ctx
from stashpad.output import emit_json

config_app = typer.Typer(help="View and manage configuration", no_args_is_help=True)


@config_app.command("show")
def config_show(ctx: typer.Context) -> None:
    """Show current configuration."""
    app_ctx = get_ctx(ctx)
    config = get_config(data_dir=app_ctx.storage.data_dir)
    if app_ctx.json_output:
        emit_json(config)
    else:
        for key, value in config.items():
            typer.echo(f"{key}: {value}")


@config_app.command("path")
def config_path(ctx: typer.Context) -> None:
    """Print the vault data directory path."""
    app_ctx = get_ctx(ctx)
    path = str(app_ctx.storage.data_dir)
    if app_ctx.json_output:
        emit_json({"data_dir": path})
    else:
        typer.echo(path)


@config_app.command("set")
def config_set(
    ctx: typer.Context,
    key: str = typer.Option(..., "--key", "-k", help="Setting name (required)"),
    value: str = typer.Option(..., "--value", "-v", prompt=True, help="Setting value"),
) -> None:
    """Set a configuration value (demo — prints guidance for .env usage)."""
    app_ctx = get_ctx(ctx)
    message = {
        "key": key,
        "value": value,
        "hint": f"Add STASH_{key.upper()}={value} to your .env file",
    }
    if app_ctx.json_output:
        emit_json(message)
    else:
        typer.echo(f"To persist, add to .env: STASH_{key.upper()}={value}")
