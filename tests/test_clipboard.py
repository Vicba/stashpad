"""Tests for clipboard read helpers."""

from __future__ import annotations

import subprocess

import pytest

from stash_cli.clipboard import copy_to_clipboard, read_from_clipboard
from stash_cli.exceptions import StashError


def test_copy_to_clipboard_darwin(monkeypatch) -> None:
    """MacOS uses pbcopy."""
    captured: dict[str, object] = {}

    def fake_run(command: list[str], /, **kwargs: object) -> None:
        captured["command"] = command
        captured["input"] = kwargs.get("input")

    monkeypatch.setattr("stash_cli.clipboard.platform.system", lambda: "Darwin")
    monkeypatch.setattr("stash_cli.clipboard.subprocess.run", fake_run)

    copy_to_clipboard("hello")
    assert captured["command"] == ["pbcopy"]
    assert captured["input"] == b"hello"


def test_read_from_clipboard_darwin(monkeypatch) -> None:
    """MacOS uses pbpaste."""
    class FakeResult:
        stdout = "clipboard text"

    def fake_run(command: list[str], /, **kwargs: object) -> FakeResult:
        assert command == ["pbpaste"]
        return FakeResult()

    monkeypatch.setattr("stash_cli.clipboard.platform.system", lambda: "Darwin")
    monkeypatch.setattr("stash_cli.clipboard.subprocess.run", fake_run)

    assert read_from_clipboard() == "clipboard text"


def test_read_from_clipboard_empty(monkeypatch) -> None:
    """Empty clipboard raises StashError."""
    class FakeResult:
        stdout = "   "

    monkeypatch.setattr("stash_cli.clipboard.platform.system", lambda: "Darwin")
    monkeypatch.setattr("stash_cli.clipboard.subprocess.run", lambda *args, **kwargs: FakeResult())

    with pytest.raises(StashError, match="Clipboard is empty"):
        read_from_clipboard()


def test_copy_to_clipboard_linux_prefers_wl_copy(monkeypatch) -> None:
    """Linux tries wl-copy before xclip."""
    calls: list[list[str]] = []

    def fake_run(command: list[str], /, **kwargs: object) -> None:
        calls.append(command)
        if command[0] == "wl-copy":
            return
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("stash_cli.clipboard.platform.system", lambda: "Linux")
    monkeypatch.setattr("stash_cli.clipboard.subprocess.run", fake_run)

    copy_to_clipboard("hello")
    assert calls == [["wl-copy"]]


def test_copy_to_clipboard_linux_falls_back_to_xclip(monkeypatch) -> None:
    """Linux falls back to xclip when wl-copy is unavailable."""
    calls: list[list[str]] = []

    def fake_run(command: list[str], /, **kwargs: object) -> None:
        calls.append(command)
        if command[0] == "xclip":
            return
        missing = "missing"
        raise OSError(missing)

    monkeypatch.setattr("stash_cli.clipboard.platform.system", lambda: "Linux")
    monkeypatch.setattr("stash_cli.clipboard.subprocess.run", fake_run)

    copy_to_clipboard("hello")
    assert calls == [["wl-copy"], ["xclip", "-selection", "clipboard"]]


def test_copy_to_clipboard_linux_missing_tools(monkeypatch) -> None:
    """Linux reports a helpful error when no clipboard tool exists."""
    def fake_run(command: list[str], /, **kwargs: object) -> None:
        missing = "missing"
        raise OSError(missing)

    monkeypatch.setattr("stash_cli.clipboard.platform.system", lambda: "Linux")
    monkeypatch.setattr("stash_cli.clipboard.subprocess.run", fake_run)

    with pytest.raises(StashError, match="No clipboard tool found"):
        copy_to_clipboard("hello")
