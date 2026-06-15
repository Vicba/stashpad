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
