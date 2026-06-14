"""Initialize the Stash vault.

Typer chapters:
- Ask with Prompt — https://typer.tiangolo.com/tutorial/prompt/
- Password CLI Option — https://typer.tiangolo.com/tutorial/options/password/
- CLI Arguments with Environment Variables — https://typer.tiangolo.com/tutorial/arguments/envvar/
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from stash_cli.context import get_ctx
from stash_cli.exceptions import StashError
from stash_cli.output import emit_json
from stash_cli.schemas import VaultInitOptions
from stash_cli.storage import VaultStorage


def _confirm_api_token(value: Optional[str]) -> Optional[str]:
    """Confirm API token entry matches (password confirmation demo).

    Parameters
    ----------
    value : str, optional
        Token from ``--api-token``.

    Returns
    -------
    str, optional
        Confirmed token.

    Raises
    ------
    typer.BadParameter
        If confirmation does not match.
    """
    if not value:
        return value
    confirmation = typer.prompt(
        "Confirm API token",
        hide_input=True,
    )
    if value != confirmation:
        raise typer.BadParameter("API tokens do not match")
    return value


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
    api_token: Optional[str] = typer.Option(
        None,
        "--api-token",
        help="Optional API token (hidden input with confirmation)",
        hide_input=True,
        callback=_confirm_api_token,
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
    api_token : str, optional
        Demo API token with confirmation (not persisted).
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
            f"Vault already exists at {app_ctx.storage.data_dir}. "
            "Use --force to re-initialize.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        options = VaultInitOptions(name=name or "default")
        vault = app_ctx.storage.initialize(options)
        if api_token and app_ctx.verbose:
            typer.echo("API token stored in session only (demo — not persisted).")
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
