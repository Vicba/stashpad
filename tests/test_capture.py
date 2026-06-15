"""Tests for quick-capture content resolution."""

from __future__ import annotations

import io

import pytest

from stashpad.capture import read_from_stdin, resolve_entry_content
from stashpad.constants import STDIN_CONTENT_ALIAS
from stashpad.exceptions import ValidationError


def test_resolve_entry_content_uses_positional_value() -> None:
    """Positional content is returned when no capture flags are set."""
    assert resolve_entry_content("docker ps") == "docker ps"


def test_resolve_entry_content_requires_source() -> None:
    """Missing content and capture flags raises a validation error."""
    with pytest.raises(ValidationError, match="Content is required"):
        resolve_entry_content(None)


def test_resolve_entry_content_rejects_both_capture_flags() -> None:
    """Clipboard and stdin capture cannot be combined."""
    with pytest.raises(ValidationError, match="only one"):
        resolve_entry_content(None, from_stdin=True, from_clipboard=True)


def test_resolve_entry_content_from_clipboard(monkeypatch) -> None:
    """Clipboard capture bypasses the positional content argument."""
    monkeypatch.setattr("stashpad.capture.read_from_clipboard", lambda: "from clipboard")
    assert resolve_entry_content(None, from_clipboard=True) == "from clipboard"


def test_read_from_stdin_reads_piped_text(monkeypatch) -> None:
    """Piped stdin is read as entry content."""
    monkeypatch.setattr("sys.stdin", io.StringIO("line one\nline two\n"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert read_from_stdin() == "line one\nline two\n"


def test_read_from_stdin_rejects_tty(monkeypatch) -> None:
    """TTY stdin without a pipe raises a validation error."""
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    with pytest.raises(ValidationError, match="No stdin available"):
        read_from_stdin()


def test_resolve_entry_content_stdin_alias(monkeypatch) -> None:
    """The '-' content alias reads from stdin."""
    monkeypatch.setattr("sys.stdin", io.StringIO("piped content"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert resolve_entry_content(STDIN_CONTENT_ALIAS) == "piped content"
