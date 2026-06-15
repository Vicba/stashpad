"""CLI output helpers for Rich tables and JSON mode."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from stash_cli.models import Entry

console = Console()


def emit_json(data: Any) -> None:
    """Print JSON to stdout.

    Parameters
    ----------
    data : Any
        JSON-serializable payload (often from ``model_dump``).

    Returns
    -------
    None

    Examples
    --------
    >>> emit_json({"status": "ok"})  # doctest: +SKIP
    """
    typer.echo(json.dumps(data, indent=2, default=str))


def render_entry_list(
    entries: list[Entry],
    *,
    json_output: bool,
    title: str = "Entries",
    empty_message: str = "No entries found.",
) -> None:
    """Print entries as JSON or a Rich table.

    Parameters
    ----------
    entries : list of Entry
        Entries to display.
    json_output : bool
        Emit JSON when ``True``.
    title : str, optional
        Table title for terminal output.
    empty_message : str, optional
        Message when there are no entries.

    Returns
    -------
    None
    """
    if json_output:
        emit_json([entry_summary(entry) for entry in entries])
    elif not entries:
        typer.echo(empty_message)
    else:
        print_entry_table(entries, title=title)


def print_entry_table(entries: list[Entry], title: str = "Entries") -> None:
    """Render entries as a Rich table.

    Parameters
    ----------
    entries : list of Entry
        Entries to display.
    title : str, optional
        Table title.

    Returns
    -------
    None
    """
    table = Table(title=title)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Pin", style="yellow", no_wrap=True)
    table.add_column("Title", style="cyan")
    table.add_column("Tags", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Updated", style="magenta")

    for entry in entries:
        short_id = str(entry.id)[:8]
        pin_marker = "★" if entry.pinned else "-"
        tags = ", ".join(entry.tags) if entry.tags else "-"
        updated = entry.updated_at.strftime("%Y-%m-%d")
        table.add_row(short_id, pin_marker, entry.title, tags, entry.priority.value, updated)

    console.print(table)


def print_entry_detail(entry: Entry) -> None:
    """Render a single entry as a Rich panel.

    Parameters
    ----------
    entry : Entry
        Entry to display.

    Returns
    -------
    None
    """
    lines = [
        f"[bold]ID:[/bold] {entry.id}",
        f"[bold]Pinned:[/bold] {'yes' if entry.pinned else 'no'}",
        f"[bold]Priority:[/bold] {entry.priority.value}",
        f"[bold]Tags:[/bold] {', '.join(entry.tags) if entry.tags else '-'}",
        f"[bold]Created:[/bold] {entry.created_at.isoformat()}",
        f"[bold]Updated:[/bold] {entry.updated_at.isoformat()}",
    ]
    if entry.url:
        lines.append(f"[bold]URL:[/bold] {entry.url}")
    lines.append("")
    lines.append(entry.content)
    console.print(Panel("\n".join(lines), title=entry.title, border_style="blue"))


def entry_summary(entry: Entry) -> dict:
    """Return a JSON-serializable entry summary.

    Parameters
    ----------
    entry : Entry
        Entry model.

    Returns
    -------
    dict
        ``entry.model_dump(mode="json")``.

    Examples
    --------
    >>> from stash_cli.models import Entry
    >>> entry_summary(Entry(title="T", content="C"))["title"]
    'T'
    """
    return entry.model_dump(mode="json")
