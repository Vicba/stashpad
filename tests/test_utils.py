"""Test export/import utilities."""

from __future__ import annotations

import json

from stash_cli.models import Entry, ExportFormat, Vault
from stash_cli.utils import export_entries, export_vault_json, parse_import_file


def test_export_json_and_markdown() -> None:
    """Export helpers produce valid output."""
    entry = Entry(title="T", content="Body", tags=["go"])
    json_out = export_entries([entry], ExportFormat.JSON)
    assert "Body" in json_out
    md_out = export_entries([entry], ExportFormat.MARKDOWN)
    assert "# Stash Export" in md_out
    assert "Body" in md_out


def test_export_vault_json() -> None:
    """Full vault JSON export is valid JSON."""
    vault = Vault()
    payload = export_vault_json(vault)
    data = json.loads(payload)
    assert "entries" in data


def test_parse_import_file(tmp_path) -> None:
    """Import parser returns Pydantic ImportPayload."""
    path = tmp_path / "entries.json"
    path.write_text(
        json.dumps([{"title": "A", "content": "B"}]),
        encoding="utf-8",
    )
    payload = parse_import_file(path)
    assert len(payload.entries) == 1
    assert payload.entries[0].title == "A"
