"""Tests for entry kind detection."""

from __future__ import annotations

from stashpad.kind import detect_entry_kind, normalize_new_entry
from stashpad.models import EntryKind


def test_detect_url_from_url_field() -> None:
    kind = detect_entry_kind(content="", url="https://example.com")
    assert kind == EntryKind.URL


def test_detect_url_from_content() -> None:
    kind = detect_entry_kind(content="https://example.com", url=None)
    assert kind == EntryKind.URL


def test_detect_command() -> None:
    kind = detect_entry_kind(content="kubectl apply -f deploy.yaml", url=None)
    assert kind == EntryKind.COMMAND


def test_detect_snippet() -> None:
    content = "def hello():\n    return 'world'\n"
    kind = detect_entry_kind(content=content, url=None)
    assert kind == EntryKind.SNIPPET


def test_detect_note_fallback() -> None:
    kind = detect_entry_kind(content="Remember to review the deploy checklist.", url=None)
    assert kind == EntryKind.NOTE


def test_explicit_kind_overrides_detection() -> None:
    kind = detect_entry_kind(content="kubectl apply -f", url=None, explicit_kind=EntryKind.NOTE)
    assert kind == EntryKind.NOTE


def test_normalize_new_entry_promotes_url_content() -> None:
    content, url, kind = normalize_new_entry(
        content="https://example.com",
        url=None,
        kind=None,
    )
    assert kind == EntryKind.URL
    assert url == "https://example.com"
    assert content == ""
