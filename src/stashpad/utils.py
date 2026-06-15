"""Shared utilities for export/import and formatting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stashpad.models import Entry, ExportFormat, Vault
from stashpad.schemas import ImportPayload


def entry_to_dict(entry: Entry) -> dict[str, Any]:
    """Serialize an entry to a plain dictionary.

    Parameters
    ----------
    entry : Entry
        Entry model to serialize.

    Returns
    -------
    dict
        JSON-compatible dictionary.

    Examples
    --------
    >>> entry_to_dict(Entry(title="T", content="C"))["title"]
    'T'
    """
    return entry.model_dump(mode="json")


def export_vault_json(vault: Vault) -> str:
    """Export the full vault as formatted JSON.

    Parameters
    ----------
    vault : Vault
        Vault to export.

    Returns
    -------
    str
        Indented JSON string.
    """
    return json.dumps(vault.model_dump(mode="json"), indent=2, ensure_ascii=False)


def export_vault_markdown(entries: list[Entry]) -> str:
    """Export entries as a Markdown document.

    Parameters
    ----------
    entries : list of Entry
        Entries to include in the export.

    Returns
    -------
    str
        Markdown document body.
    """
    lines = ["# Stash Export", ""]
    for entry in entries:
        lines.append(f"## {entry.title}")
        lines.append("")
        lines.append(f"- **ID:** `{entry.id}`")
        lines.append(f"- **Priority:** {entry.priority.value}")
        if entry.tags:
            lines.append(f"- **Tags:** {', '.join(entry.tags)}")
        if entry.url:
            lines.append(f"- **URL:** {entry.url}")
        lines.append("")
        lines.append("```")
        lines.append(entry.content)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def export_entries(entries: list[Entry], fmt: ExportFormat) -> str:
    """Export entries in the requested format.

    Parameters
    ----------
    entries : list of Entry
        Entries to export.
    fmt : ExportFormat
        Target format (``json`` or ``markdown``).

    Returns
    -------
    str
        Serialized export content.

    Examples
    --------
    >>> "Docker" in export_entries([Entry(title="Docker", content="cmd")], ExportFormat.MARKDOWN)
    True
    """
    if fmt == ExportFormat.JSON:
        payload = [entry_to_dict(entry) for entry in entries]
        return json.dumps(payload, indent=2, ensure_ascii=False)
    return export_vault_markdown(entries)


def parse_import_file(path: Path) -> ImportPayload:
    """Load and validate entries from a JSON import file.

    Parameters
    ----------
    path : Path
        Path to a JSON file (list of entries or vault object).

    Returns
    -------
    ImportPayload
        Pydantic-validated import payload.

    Raises
    ------
    ValueError
        If JSON shape is invalid.
    pydantic.ValidationError
        If entry fields fail validation.

    Examples
    --------
    >>> from pathlib import Path
    >>> # parse_import_file(Path("entries.json")).entries[0].title
    """
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return ImportPayload.from_raw(data)
