"""Detect and normalize entry ``kind`` (command, url, snippet, note).

Detection order when ``--kind`` is omitted on ``stash entry add``:

1. ``url`` — URL field only, or content is a single http(s) link
2. ``command`` — shell prefixes (``git``, ``kubectl``, …), pipes, flags
3. ``snippet`` — code fences, indentation, or code keywords
4. ``note`` — everything else

See ``detect_entry_kind`` for the public API used at create time.
Legacy vault entries without ``kind`` are resolved again at use time in
``entry_actions.resolve_entry_kind``.
"""

from __future__ import annotations

import re

from stash_cli.models import EntryKind
from stash_cli.validators import validate_http_url

# Shell commands stash recognizes when auto-detecting ``kind: command``.
_SHELL_COMMAND_PREFIXES = (
    "git ",
    "docker ",
    "kubectl ",
    "npm ",
    "pnpm ",
    "yarn ",
    "poetry ",
    "python ",
    "pip ",
    "curl ",
    "ssh ",
    "cd ",
    "export ",
    "make ",
    "cargo ",
    "go ",
    "echo ",
    "./",
    "../",
    "~/",
)

# Tokens that suggest a shell pipeline or redirect.
_SHELL_OPERATOR_TOKENS = ("|", "&&", ";", ">>", ">")


def detect_entry_kind(
    *,
    content: str,
    url: str | None,
    explicit_kind: EntryKind | None = None,
) -> EntryKind:
    """Auto-detect entry kind from content and URL.

    Parameters
    ----------
    content : str
        Entry body text.
    url : str, optional
        Optional related URL from ``--url``.
    explicit_kind : EntryKind, optional
        User-provided ``--kind``; returned unchanged when set.

    Returns
    -------
    EntryKind
        One of ``command``, ``url``, ``snippet``, or ``note``.

    Examples
    --------
    >>> detect_entry_kind(content="", url="https://example.com")
    <EntryKind.URL: 'url'>
    >>> detect_entry_kind(content="kubectl apply -f", url=None)
    <EntryKind.COMMAND: 'command'>
    """
    if explicit_kind is not None:
        return explicit_kind

    body = content.strip()
    link = (url or "").strip()

    # Checked before command/snippet so a bare bookmark wins over shell-like URLs.
    if link and not body:
        return EntryKind.URL
    if body and _content_is_only_url(body):
        return EntryKind.URL
    # Command before snippet: "kubectl apply" should not become a code block.
    if body and _content_looks_like_shell_command(body):
        return EntryKind.COMMAND
    if body and _content_looks_like_code_snippet(body):
        return EntryKind.SNIPPET
    return EntryKind.NOTE


def normalize_new_entry(
    *,
    content: str,
    url: str | None,
    kind: EntryKind | None,
) -> tuple[str, str | None, EntryKind]:
    """Resolve kind and normalize fields before saving a new entry.

    When content is a lone URL, moves it into the ``url`` field and clears
    content so the stored entry matches ``kind: url``.

    Parameters
    ----------
    content : str
        Raw entry body from the CLI.
    url : str, optional
        Raw ``--url`` value.
    kind : EntryKind, optional
        Explicit ``--kind`` from the CLI.

    Returns
    -------
    tuple of (str, str or None, EntryKind)
        Normalized ``(content, url, kind)`` ready for ``EntryCreate``.
    """
    resolved_kind = detect_entry_kind(content=content, url=url, explicit_kind=kind)
    # User pasted a URL into the body — store it in the url field, not content.
    if resolved_kind == EntryKind.URL and not url and _content_is_only_url(content):
        return "", content.strip(), resolved_kind
    return content, url, resolved_kind


def _content_is_only_url(text: str) -> bool:
    """Return True when *text* is a single line containing only an http(s) URL."""
    stripped = text.strip()
    # Multi-line text is never treated as a lone URL bookmark.
    if not stripped or "\n" in stripped:
        return False
    try:
        validate_http_url(stripped)
    except ValueError:
        return False
    return True


def _content_looks_like_shell_command(content: str) -> bool:
    """Return True when *content* looks like a shell command or script."""
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    if not lines:
        return False

    command_like_lines = 0
    for line in lines:
        # Allow commented lines in shell scripts without counting against the ratio.
        if line.startswith("#"):
            continue
        lower = line.lower()
        if (
            lower.startswith(_SHELL_COMMAND_PREFIXES)
            or any(token in line for token in _SHELL_OPERATOR_TOKENS)
            or re.match(r"^[\w./~-]+(\s+-[\w-]+|\s+--[\w-]+)", line)
        ):
            command_like_lines += 1

    # One line must look like a command; multi-line scripts need a majority.
    if len(lines) == 1:
        return command_like_lines == 1
    return command_like_lines >= max(1, len(lines) // 2)


def _content_looks_like_code_snippet(content: str) -> bool:
    """Return True when *content* looks like source code rather than prose."""
    if "```" in content:
        return True

    lines = content.splitlines()
    # Two or more indented lines usually means a pasted code block.
    indented_lines = sum(1 for line in lines if line.startswith(("    ", "\t")))
    if indented_lines >= 2:
        return True

    code_markers = ("def ", "class ", "import ", "function ", "const ", "fn ")
    marker_hits = sum(1 for marker in code_markers if marker in content)
    # Two markers = clearly code; one marker + multiple lines = likely a function.
    return marker_hits >= 2 or (marker_hits >= 1 and len(lines) >= 2)
