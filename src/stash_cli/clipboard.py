"""Cross-platform clipboard helpers."""

from __future__ import annotations

import platform
import subprocess

from stash_cli.exceptions import StashError


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard.

    Parameters
    ----------
    text : str
        Text to place on the clipboard.

    Raises
    ------
    StashError
        If no clipboard tool is available or the copy fails.

    Examples
    --------
    >>> copy_to_clipboard("hello")  # doctest: +SKIP
    """
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        elif system == "Linux":
            _copy_linux(text)
        elif system == "Windows":
            subprocess.run(
                ["clip"],
                input=text.encode("utf-16le"),
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
            )
        else:
            msg = f"Clipboard not supported on {system}"
            raise StashError(msg)
    except (OSError, subprocess.CalledProcessError) as exc:
        msg = "Failed to copy to clipboard"
        raise StashError(msg) from exc


        raise StashError(msg) from exc


def read_from_clipboard() -> str:
    """Read text from the system clipboard.

    Returns
    -------
    str
        Clipboard text as UTF-8.

    Raises
    ------
    StashError
        If no clipboard tool is available, read fails, or clipboard is empty.

    Examples
    --------
    >>> read_from_clipboard()  # doctest: +SKIP
    """
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                check=True,
                text=True,
            )
            text = result.stdout
        elif system == "Linux":
            text = _read_linux()
        elif system == "Windows":
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                check=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
            )
            text = result.stdout
        else:
            msg = f"Clipboard not supported on {system}"
            raise StashError(msg)
    except (OSError, subprocess.CalledProcessError) as exc:
        msg = "Failed to read from clipboard"
        raise StashError(msg) from exc

    if not text.strip():
        msg = "Clipboard is empty"
        raise StashError(msg)
    return text


def _read_linux() -> str:
    """Try Wayland and X11 clipboard tools on Linux."""
    try:
        result = subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True,
                check=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            msg = "No clipboard tool found (install wl-clipboard or xclip)"
            raise StashError(msg) from exc
    return result.stdout


def _copy_linux(text: str) -> None:
    """Try Wayland and X11 clipboard tools on Linux."""
    encoded = text.encode("utf-8")
    try:
        subprocess.run(["wl-copy"], input=encoded, check=True)
    except (OSError, subprocess.CalledProcessError):
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=encoded,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            msg = "No clipboard tool found (install wl-clipboard or xclip)"
            raise StashError(msg) from exc
