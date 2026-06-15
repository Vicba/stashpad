"""Initialize the Stash vault.

Typer chapters:
- Ask with Prompt — https://typer.tiangolo.com/tutorial/prompt/
- CLI Arguments with Environment Variables — https://typer.tiangolo.com/tutorial/arguments/envvar/
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from stash_cli.constants import DEFAULT_VAULT_NAME
from stash_cli.context import get_ctx
from stash_cli.exceptions import StashError
from stash_cli.output import emit_json
from stash_cli.schemas import VaultInitOptions
from stash_cli.storage import VaultStorage


def init(
    ctx: typer.Context,
    data_dir: Optional[Path] = typer.Argument(
        None,
        help="Vault directory (defaults to STASH_DATA_DIR or ~/.config/stash)",
        envvar="STASH_DATA_DIR",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Vault display name",
        prompt="Vault name",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Re-initialize even if vault exists",
    ),
) -> None:
    """Create and initialize a new Stash vault.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    data_dir : Path, optional
        Vault directory; reads ``STASH_DATA_DIR`` env var.
    name : str, optional
        Vault display name; prompts if omitted.
    force : bool
        Overwrite existing vault.

    Returns
    -------
    None

    Examples
    --------
    $ stash init --name work
    $ STASH_DATA_DIR=/tmp/stash stash init --force
    """
    app_ctx = get_ctx(ctx)
    if data_dir is not None:
        app_ctx.storage = VaultStorage(data_dir)

    if app_ctx.storage.is_initialized and not force:
        typer.echo(
            f"Vault already exists at {app_ctx.storage.data_dir}. Use --force to re-initialize.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        options = VaultInitOptions(name=name or DEFAULT_VAULT_NAME)
        vault = app_ctx.storage.initialize(options)
        message = {
            "status": "initialized",
            "name": vault.metadata.name,
            "path": str(app_ctx.storage.data_dir),
        }
        if app_ctx.json_output:
            emit_json(message)
        else:
            typer.echo(f"Vault '{vault.metadata.name}' initialized at {app_ctx.storage.data_dir}")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc
