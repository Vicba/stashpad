"""Stash CLI entry point.

Typer chapters:
- Typer App — https://typer.tiangolo.com/tutorial/typer-app/
- One File Per Command — https://typer.tiangolo.com/tutorial/one-file-per-command/
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from stash_cli.commands.config_cmd import config_app
from stash_cli.commands.entry import entry_app
from stash_cli.commands.export import export_app
from stash_cli.commands.import_cmd import import_entries
from stash_cli.commands.init import init
from stash_cli.commands.open_cmd import open_entry
from stash_cli.commands.search import search
from stash_cli.commands.tags import tags_app
from stash_cli.context import build_context, version_callback

app = typer.Typer(
    name="stash",
    help="Stash — personal developer reference manager.",
    no_args_is_help=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
    config_dir: Optional[Path] = typer.Option(
        None,
        "--config-dir",
        help="Override vault data directory",
        envvar="STASH_DATA_DIR",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Stash global options shared by all commands."""
    ctx.obj = build_context(verbose=verbose, json_output=json_output, config_dir=config_dir)


app.command("init")(init)
app.command("search")(search)
app.command("import")(import_entries)
app.command("open")(open_entry)

app.add_typer(entry_app, name="entry")
app.add_typer(tags_app, name="tags")
app.add_typer(export_app, name="export")
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
