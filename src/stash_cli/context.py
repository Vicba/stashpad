"""Global CLI context and root callback.

Typer chapters:
- Typer Callback — https://typer.tiangolo.com/tutorial/commands/callback/
- Using the Context — https://typer.tiangolo.com/tutorial/commands/context/
- Version CLI Option — https://typer.tiangolo.com/tutorial/options/version/
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from pydantic import ConfigDict
from pydantic import BaseModel

from stash_cli import __version__
from stash_cli.config import get_settings
from stash_cli.storage import VaultStorage


class AppContext(BaseModel):
    """Shared state passed to all commands via ``ctx.obj``.

    Parameters
    ----------
    verbose : bool
        Enable verbose stderr output.
    json_output : bool
        Emit JSON to stdout instead of Rich formatting.
    storage : VaultStorage
        Vault read/write handle for this invocation.
    tag_prefix : str, optional
        Tag prefix filter applied by the tags subcommand group.

    Examples
    --------
    >>> ctx = AppContext(verbose=True, json_output=False, storage=VaultStorage(Path("/tmp/x")))
    >>> ctx.verbose
    True
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    verbose: bool = False
    json_output: bool = False
    storage: VaultStorage
    tag_prefix: Optional[str] = None


def version_callback(value: bool) -> None:
    """Print version and exit when ``--version`` is passed.

    Parameters
    ----------
    value : bool
        Whether ``--version`` was invoked (Typer callback convention).

    Returns
    -------
    None
        Always raises ``typer.Exit`` when ``value`` is truthy.

    Examples
    --------
    >>> # Invoked automatically by Typer when user runs: stash --version
    """
    if value:
        typer.echo(f"stash version {__version__}")
        raise typer.Exit()


def build_context(
    verbose: bool = False,
    json_output: bool = False,
    config_dir: Optional[Path] = None,
) -> AppContext:
    """Construct ``AppContext`` from global CLI options.

    Parameters
    ----------
    verbose : bool, optional
        Verbose flag from ``--verbose``.
    json_output : bool, optional
        JSON mode from ``--json``.
    config_dir : Path, optional
        Override for ``STASH_DATA_DIR``.

    Returns
    -------
    AppContext
        Populated context for the current CLI invocation.

    Examples
    --------
    >>> ctx = build_context(json_output=True)
    >>> ctx.json_output
    True
    """
    settings = get_settings(data_dir=config_dir)
    storage = VaultStorage(settings.data_dir)
    return AppContext(verbose=verbose, json_output=json_output, storage=storage)


def get_ctx(ctx: typer.Context) -> AppContext:
    """Return ``AppContext`` from Typer context.

    Parameters
    ----------
    ctx : typer.Context
        Active Typer context.

    Returns
    -------
    AppContext
        Shared application context.

    Raises
    ------
    typer.Exit
        If ``ctx.obj`` is missing or not an ``AppContext``.
    """
    if ctx.obj is None or not isinstance(ctx.obj, AppContext):
        raise typer.Exit(code=1)
    return ctx.obj
