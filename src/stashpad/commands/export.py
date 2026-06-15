"""Export vault data.

Typer chapters:
- Path — https://typer.tiangolo.com/tutorial/parameter-types/path/
- Progress Bar — https://typer.tiangolo.com/tutorial/progressbar/
"""

from __future__ import annotations

import time
from pathlib import Path

import typer
from rich.progress import BarColumn, Progress, TextColumn

from stashpad.context import get_ctx
from stashpad.exceptions import StashError
from stashpad.models import ExportFormat
from stashpad.output import emit_json
from stashpad.utils import export_entries

export_app = typer.Typer(help="Export vault data", no_args_is_help=True)


@export_app.command("json")
def export_json(
    ctx: typer.Context,
    output: Path = typer.Argument(..., help="Output file path", dir_okay=False),
    all_entries: bool = typer.Option(
        True,
        "--all/--filtered",
        help="Export all entries (with progress for large vaults)",
    ),
) -> None:
    """Export entries as JSON."""
    _run_export(ctx, ExportFormat.JSON, output, all_entries)


@export_app.command("markdown")
def export_markdown(
    ctx: typer.Context,
    output: Path = typer.Argument(..., help="Output file path", dir_okay=False),
    all_entries: bool = typer.Option(True, "--all/--filtered"),
) -> None:
    """Export entries as Markdown."""
    _run_export(ctx, ExportFormat.MARKDOWN, output, all_entries)


def _run_export(
    ctx: typer.Context,
    fmt: ExportFormat,
    output: Path,
    all_entries: bool,
) -> None:
    app_ctx = get_ctx(ctx)
    try:
        entries = app_ctx.storage.list_entries() if all_entries else []
        if all_entries and len(entries) > 10:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                transient=True,
            ) as progress:
                task = progress.add_task("Exporting...", total=len(entries))
                for _ in entries:
                    time.sleep(0.01)
                    progress.advance(task)

        content = export_entries(entries, fmt)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")

        if app_ctx.json_output:
            emit_json({"path": str(output), "format": fmt.value, "count": len(entries)})
        else:
            typer.echo(f"Exported {len(entries)} entries to {output}")
    except StashError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(code=exc.exit_code) from exc
