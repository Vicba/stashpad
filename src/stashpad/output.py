"""CLI output helpers for Rich tables and JSON mode."""

from __future__ import annotations

import json
from typing import Any

import typer
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from stashpad.models import Entry, EntryKind

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
    table.add_column("Kind", style="blue", no_wrap=True)
    table.add_column("Title", style="cyan", no_wrap=True)
    table.add_column("Tags", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Updated", style="magenta")

    for entry in entries:
        short_id = str(entry.id)[:8]
        pin_marker = "★" if entry.pinned else "-"
        tags = ", ".join(entry.tags) if entry.tags else "-"
        updated = entry.updated_at.strftime("%Y-%m-%d")
        table.add_row(
            short_id,
            pin_marker,
            entry.kind.value,
            entry.title,
            tags,
            entry.priority.value,
            updated,
        )

    console.print(table)


def _syntax_lexer_for_snippet(entry: Entry) -> str:
    """Pick a Pygments lexer name for ``snippet`` entry content."""
    content = entry.content
    # Lightweight keyword sniffing — good enough for terminal display.
    if "def " in content or "import " in content or "class " in content:
        return "python"
    if "function " in content or "const " in content or "let " in content:
        return "javascript"
    if entry.content.strip().startswith("{") or entry.content.strip().startswith("["):
        return "json"
    return "text"


def _render_entry_body_by_kind(entry: Entry) -> RenderableType:
    """Render entry body with syntax highlighting or links based on ``entry.kind``."""
    if entry.kind == EntryKind.SNIPPET and entry.content.strip():
        return Syntax(
            entry.content,
            _syntax_lexer_for_snippet(entry),
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
    if entry.kind == EntryKind.COMMAND and entry.content.strip():
        return Syntax(entry.content, "bash", theme="monokai", word_wrap=True)
    if entry.kind == EntryKind.URL:
        lines = []
        if entry.url:
            lines.append(f"[link={entry.url}]{entry.url}[/link]")
        # URL entries may still have notes in the body (shown below the link).
        if entry.content.strip():
            lines.append("")
            lines.append(entry.content)
        return "\n".join(lines) if lines else "[dim]No URL[/dim]"
    if entry.content.strip():
        return entry.content
    return "[dim]No content[/dim]"


def print_entry_detail(entry: Entry) -> None:
    """Render a single entry as a Rich panel with kind-specific body formatting.

    Snippets and commands use syntax highlighting; URL entries show a clickable
    link; notes render as plain text.
    """
    lines = [
        f"[bold]ID:[/bold] {entry.id}",
        f"[bold]Kind:[/bold] {entry.kind.value}",
        f"[bold]Pinned:[/bold] {'yes' if entry.pinned else 'no'}",
        f"[bold]Priority:[/bold] {entry.priority.value}",
        f"[bold]Tags:[/bold] {', '.join(entry.tags) if entry.tags else '-'}",
        f"[bold]Created:[/bold] {entry.created_at.isoformat()}",
        f"[bold]Updated:[/bold] {entry.updated_at.isoformat()}",
    ]
    # For non-URL kinds, show url as metadata; URL kind renders it in the body.
    if entry.url and entry.kind != EntryKind.URL:
        lines.append(f"[bold]URL:[/bold] {entry.url}")

    body = _render_entry_body_by_kind(entry)
    console.print(
        Panel(
            Group(*lines, "", body),
            title=entry.title,
            border_style="blue",
        )
    )


def entry_summary(entry: Entry) -> dict[str, Any]:
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
    >>> from stashpad.models import Entry
    >>> entry_summary(Entry(title="T", content="C"))["title"]
    'T'
    """
    return entry.model_dump(mode="json")
