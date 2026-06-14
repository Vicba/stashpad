"""Import entries into the vault.

Typer chapters:
- File — https://typer.tiangolo.com/tutorial/parameter-types/file/
- Exceptions and Errors — https://typer.tiangolo.com/tutorial/exceptions/
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

import typer
from pydantic import ValidationError as PydanticValidationError
from rich.progress import BarColumn, Progress, TextColumn

from stash_cli.context import get_ctx
from stash_cli.exceptions import StashError, ValidationError
from stash_cli.models import Entry
from stash_cli.output import emit_json
from stash_cli.utils import parse_import_file


def import_entries(
    ctx: typer.Context,
    from_file: Optional[Path] = typer.Option(
        None,
        "--from-file",
        "-f",
        help="JSON file to import",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    directory: Optional[Path] = typer.Option(
        None,
        "--directory",
        "-d",
        help="Directory of JSON files to import",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without importing"),
) -> None:
    """Import Pydantic-validated entries from JSON file(s).

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    from_file : Path, optional
        Single JSON file to import.
    directory : Path, optional
        Directory of ``*.json`` files.
    dry_run : bool
        Validate only; do not write vault.

    Returns
    -------
    None

    Examples
    --------
    $ stash import --from-file ./backup.json
    $ stash import --directory ./exports/ --dry-run
    """
    app_ctx = get_ctx(ctx)

    if from_file is None and directory is None:
        typer.echo("Provide --from-file or --directory.", err=True)
        raise typer.Exit(code=1)

    files: List[Path] = []
    if from_file:
        files.append(from_file)
    if directory:
        files.extend(sorted(directory.glob("*.json")))

    if not files:
        typer.echo("No JSON files found to import.", err=True)
        raise typer.Exit(code=1)

    try:
        vault = app_ctx.storage.require_vault()
        imported = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Importing...", total=len(files))
            for path in files:
                payload = parse_import_file(path)
                for item in payload.entries:
                    entry = Entry.model_validate(item.model_dump())
                    if not dry_run:
                        vault.entries.append(entry)
                        app_ctx.storage.merge_tags(vault, entry.tags)
                    imported += 1
                progress.advance(task)
                time.sleep(0.05)

        if not dry_run:
            app_ctx.storage.save(vault)

        result = {"imported": imported, "dry_run": dry_run, "files": len(files)}
        if app_ctx.json_output:
            emit_json(result)
        else:
            action = "Would import" if dry_run else "Imported"
            typer.echo(f"{action} {imported} entries from {len(files)} file(s).")
    except (StashError, ValidationError, ValueError, PydanticValidationError) as exc:
        if isinstance(exc, StashError):
            message, code = exc.message, exc.exit_code
        else:
            message, code = str(exc), ValidationError.exit_code
        typer.echo(message, err=True)
        raise typer.Exit(code=code) from exc
