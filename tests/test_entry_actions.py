"""Tests for kind-aware entry actions."""

from __future__ import annotations

import pytest

from stash_cli.entry_actions import (
    execute_entry_command,
    get_clipboard_text,
    open_entry_in_browser,
    resolve_entry_kind,
)
from stash_cli.exceptions import ValidationError
from stash_cli.models import Entry, EntryKind


def test_legacy_command_resolved_at_use_time() -> None:
    """Entries saved before kind existed still run when content looks like a command."""
    entry = Entry(title="Deploy", content="kubectl apply -f", kind=EntryKind.NOTE)
    assert resolve_entry_kind(entry) == EntryKind.COMMAND


def test_get_clipboard_text_for_url_entry() -> None:
    entry = Entry(
        title="Docs",
        content="optional notes",
        url="https://example.com",
        kind=EntryKind.URL,
    )
    assert get_clipboard_text(entry) == "https://example.com"


def test_get_clipboard_text_honors_first_line_only() -> None:
    entry = Entry(
        title="Deploy",
        content="kubectl apply -f\necho done",
        kind=EntryKind.COMMAND,
    )
    assert get_clipboard_text(entry, first_line_only=True) == "kubectl apply -f"
    assert get_clipboard_text(entry) == "kubectl apply -f\necho done"


def test_execute_entry_command_rejects_note() -> None:
    entry = Entry(title="Memo", content="plain note", kind=EntryKind.NOTE)
    with pytest.raises(ValidationError, match="not a command"):
        execute_entry_command(entry, force=True)


def test_open_entry_in_browser_rejects_command() -> None:
    entry = Entry(
        title="Deploy",
        content="kubectl apply -f",
        url="https://example.com",
        kind=EntryKind.COMMAND,
    )
    with pytest.raises(ValidationError, match="not a URL"):
        open_entry_in_browser(entry)
