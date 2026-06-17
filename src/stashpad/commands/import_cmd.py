"""Import entries into the vault.

Typer chapters:
- File — https://typer.tiangolo.com/tutorial/parameter-types/file/
- Exceptions and Errors — https://typer.tiangolo.com/tutorial/exceptions/
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer
from pydantic import ValidationError as PydanticValidationError
from rich.progress import BarColumn, Progress, TextColumn

from stashpad.context import AppContext, get_ctx
from stashpad.duplicates import (
    DuplicateCandidate,
    duplicate_candidate_summary,
    find_duplicate_candidates,
    format_duplicate_match,
)
from stashpad.exceptions import StashError, ValidationError
from stashpad.models import Entry
from stashpad.output import emit_json
from stashpad.utils import parse_import_file

if TYPE_CHECKING:
    from stashpad.models import Vault
    from stashpad.storage import VaultStorage


@dataclass
class ImportRunResult:
    """Summary of a completed import run."""

    imported: int
    skipped_duplicates: int
    skipped_matches: list[DuplicateCandidate]
    file_count: int


def _resolve_import_files(
    from_file: Path | None,
    directory: Path | None,
) -> list[Path]:
    """Collect JSON import files from CLI options."""
    if from_file is None and directory is None:
        typer.echo("Provide --from-file or --directory.", err=True)
        raise typer.Exit(code=1)

    files: list[Path] = []
    if from_file:
        files.append(from_file)
    if directory:
        files.extend(sorted(directory.glob("*.json")))

    if not files:
        typer.echo("No JSON files found to import.", err=True)
        raise typer.Exit(code=1)
    return files


def _import_entries_from_files(
    storage: VaultStorage,
    vault: Vault,
    files: list[Path],
    *,
    dry_run: bool,
    ignore_duplicates: bool,
) -> ImportRunResult:
    """Import entries from JSON files and return a run summary."""
    imported = 0
    skipped_duplicates = 0
    skipped_matches: list[DuplicateCandidate] = []
    imported_this_run: list[Entry] = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("Importing...", total=len(files))
        for path in files:
            payload = parse_import_file(path)
            for item in payload.entries:
                # Compare against vault entries and items already accepted in this import.
                candidates = find_duplicate_candidates(
                    item,
                    vault.entries + imported_this_run,
                )
                if candidates and not ignore_duplicates:
                    skipped_duplicates += 1
                    skipped_matches.append(candidates[0])
                    continue

                entry = Entry.model_validate(item.model_dump())
                if not dry_run:
                    vault.entries.append(entry)
                    storage.merge_tags(vault, entry.tags)
                imported_this_run.append(entry)
                imported += 1
            progress.advance(task)
            time.sleep(0.05)

    if not dry_run:
        storage.save(vault)

    return ImportRunResult(
        imported=imported,
        skipped_duplicates=skipped_duplicates,
        skipped_matches=skipped_matches,
        file_count=len(files),
    )


def _emit_import_result(app_ctx: AppContext, run: ImportRunResult, *, dry_run: bool) -> None:
    """Print import summary as JSON or human-readable output."""
    result = {
        "imported": run.imported,
        "skipped_duplicates": run.skipped_duplicates,
        "dry_run": dry_run,
        "files": run.file_count,
        "duplicates": [duplicate_candidate_summary(match) for match in run.skipped_matches],
    }
    if app_ctx.json_output:
        emit_json(result)
        return

    action = "Would import" if dry_run else "Imported"
    typer.echo(f"{action} {run.imported} entries from {run.file_count} file(s).", err=False)
    if run.skipped_duplicates:
        typer.echo(f"Skipped {run.skipped_duplicates} duplicates.")
        for match in run.skipped_matches:
            typer.echo(f"  - {format_duplicate_match(match)}")


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
    ignore_duplicates: bool = typer.Option(
        False,
        "--ignore-duplicates",
        help="Import entries even when similar to existing vault entries",
    ),
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
    ignore_duplicates : bool
        Import entries even when similar to existing vault entries.

    Returns
    -------
    None

    Examples
    --------
    $ stash import --from-file ./backup.json
    $ stash import --directory ./exports/ --dry-run
    """
    app_ctx = get_ctx(ctx)
    files = _resolve_import_files(from_file, directory)

    try:
        vault = app_ctx.storage.require_vault()
        run = _import_entries_from_files(
            app_ctx.storage,
            vault,
            files,
            dry_run=dry_run,
            ignore_duplicates=ignore_duplicates,
        )
        _emit_import_result(app_ctx, run, dry_run=dry_run)
    except (StashError, ValidationError, ValueError, PydanticValidationError) as exc:
        if isinstance(exc, StashError):
            message, code = exc.message, exc.exit_code
        else:
            message, code = str(exc), ValidationError.exit_code
        typer.echo(message, err=True)
        raise typer.Exit(code=code) from exc
