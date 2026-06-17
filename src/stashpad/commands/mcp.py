"""``stash mcp`` — Model Context Protocol server for AI assistants."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import typer

from stashpad.context import get_ctx
from stashpad.exceptions import StashError, ValidationError
from stashpad.storage import VaultStorage

if TYPE_CHECKING:
    from collections.abc import Callable

mcp_app = typer.Typer(help="Model Context Protocol integration", no_args_is_help=True)

MCP_INSTALL_HINT = "MCP not installed. Run: poetry install -E mcp"
MCP_PYTHON_VERSION_HINT = "MCP requires Python 3.10 or newer."
VAULT_NOT_INITIALIZED_HINT = "Vault not initialized. Run: stash init"


def _import_mcp_server_runner() -> Callable[..., None]:
    """Import ``run_mcp_server`` lazily so the core CLI works without the MCP extra."""
    from stashpad.mcp.server import run_mcp_server

    return run_mcp_server


def _require_python_3_10() -> None:
    """Exit when the host Python is too old for the MCP SDK."""
    if sys.version_info < (3, 10):
        typer.echo(MCP_PYTHON_VERSION_HINT, err=True)
        raise typer.Exit(code=1)


def _require_initialized_vault(storage: VaultStorage) -> None:
    """Exit when no vault exists at the configured data directory."""
    if not storage.is_initialized:
        typer.echo(VAULT_NOT_INITIALIZED_HINT, err=True)
        raise typer.Exit(code=2)


def _handle_mcp_error(exc: StashError | ValidationError) -> None:
    """Print a stash error and exit with its mapped code."""
    typer.echo(exc.message, err=True)
    raise typer.Exit(code=exc.exit_code) from exc


@mcp_app.command("serve")
def serve(
    ctx: typer.Context,
    read_only: bool = typer.Option(
        False,
        "--read-only",
        help="Expose only read tools (search, list, get); omit stash_add",
    ),
) -> None:
    """Run the Stashpad MCP server over stdio for Cursor, Claude Desktop, etc.

    The AI client spawns this process and communicates via stdin/stdout.
    Configure ``STASH_DATA_DIR`` or ``--config-dir`` to select the vault.

    Examples
    --------
    $ stash mcp serve
    $ stash mcp serve --read-only
    $ stash --config-dir ~/.config/stash mcp serve
    """
    _require_python_3_10()
    app_ctx = get_ctx(ctx)

    if app_ctx.json_output:
        typer.echo("--json is not supported with mcp serve", err=True)
        raise typer.Exit(code=1)

    try:
        run_mcp_server = _import_mcp_server_runner()
    except ImportError:
        typer.echo(MCP_INSTALL_HINT, err=True)
        raise typer.Exit(code=1) from None

    storage = app_ctx.storage
    _require_initialized_vault(storage)

    try:
        # Blocks until the MCP client closes the stdio session.
        run_mcp_server(storage, read_only=read_only)
    except (ValidationError, StashError) as exc:
        _handle_mcp_error(exc)
