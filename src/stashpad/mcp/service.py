"""Business logic for Stashpad MCP tools.

MCP tool handlers in :mod:`stashpad.mcp.server` stay thin; this module owns
vault reads and writes via :class:`VaultMcpService`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from pydantic import ValidationError as PydanticValidationError

from stashpad.constants import DEFAULT_LIST_LIMIT, DEFAULT_SEARCH_LIMIT
from stashpad.exceptions import StashError, ValidationError
from stashpad.kind import normalize_new_entry
from stashpad.models import Entry, EntryKind, SortOrder
from stashpad.output import entry_summary
from stashpad.schemas import EntryCreate, EntryFilter, SearchQuery

if TYPE_CHECKING:
    from collections.abc import Callable

    from stashpad.storage import VaultStorage

T = TypeVar("T")

# JSON keys returned to MCP clients (match ``stash --json`` entry shapes).
ENTRIES_KEY = "entries"
ENTRY_KEY = "entry"
COUNT_KEY = "count"


def format_entry_list_response(entries: list[Entry]) -> dict[str, Any]:
    """Build the standard list/search tool response payload.

    Parameters
    ----------
    entries : list of Entry
        Vault entries to serialize.

    Returns
    -------
    dict
        ``{"entries": [...], "count": N}`` with JSON-safe entry dicts.
    """
    return {
        ENTRIES_KEY: [entry_summary(entry) for entry in entries],
        COUNT_KEY: len(entries),
    }


def format_single_entry_response(entry: Entry) -> dict[str, Any]:
    """Build the standard get/add tool response payload.

    Parameters
    ----------
    entry : Entry
        Vault entry to serialize.

    Returns
    -------
    dict
        ``{"entry": {...}}`` with a JSON-safe entry dict.
    """
    return {ENTRY_KEY: entry_summary(entry)}


def parse_entry_uuid(entry_id: str) -> UUID:
    """Validate and parse an entry UUID from MCP tool input.

    Parameters
    ----------
    entry_id : str
        UUID string from the assistant.

    Returns
    -------
    UUID
        Parsed entry identifier.

    Raises
    ------
    ValidationError
        When *entry_id* is not a valid UUID.
    """
    try:
        return UUID(entry_id)
    except ValueError as exc:
        msg = f"Invalid entry ID '{entry_id}'. Expected a UUID."
        raise ValidationError(msg) from exc


def parse_entry_kind(kind: str | None) -> EntryKind | None:
    """Parse an optional entry kind string from MCP tool input.

    Parameters
    ----------
    kind : str, optional
        One of ``command``, ``url``, ``snippet``, or ``note``.

    Returns
    -------
    EntryKind, optional
        Parsed kind, or ``None`` when omitted.

    Raises
    ------
    ValidationError
        When *kind* is not a recognized value.
    """
    if kind is None:
        return None
    try:
        return EntryKind(kind)
    except ValueError as exc:
        msg = f"Invalid kind '{kind}'. Use command, url, snippet, or note."
        raise ValidationError(msg) from exc


def parse_list_sort_order(sort: str) -> SortOrder:
    """Parse list sort order from MCP tool input.

    Parameters
    ----------
    sort : str
        One of ``newest``, ``oldest``, or ``title``.

    Returns
    -------
    SortOrder
        Parsed sort order.

    Raises
    ------
    ValidationError
        When *sort* is not a recognized value.
    """
    try:
        return SortOrder(sort)
    except ValueError as exc:
        msg = f"Invalid sort '{sort}'. Use newest, oldest, or title."
        raise ValidationError(msg) from exc


def format_vault_error(exc: Exception) -> str:
    """Turn storage or schema errors into assistant-friendly messages.

    Parameters
    ----------
    exc : Exception
        Error raised by vault I/O or Pydantic validation.

    Returns
    -------
    str
        Message suitable for MCP tool error responses.
    """
    if isinstance(exc, StashError):
        return exc.message
    if isinstance(exc, PydanticValidationError):
        return str(exc)
    return str(exc)


def run_vault_operation(operation: Callable[[], T]) -> T:
    """Execute a vault call and map failures to :class:`ValidationError`.

    MCP tools should surface predictable errors instead of raw tracebacks.

    Parameters
    ----------
    operation : callable
        Zero-argument callable that performs one vault operation.

    Returns
    -------
    T
        Return value from *operation*.

    Raises
    ------
    ValidationError
        When the vault call raises :class:`StashError` or Pydantic validation fails.
    """
    try:
        return operation()
    except (StashError, PydanticValidationError) as exc:
        raise ValidationError(format_vault_error(exc)) from exc


@dataclass
class VaultMcpService:
    """Vault operations backing Stashpad MCP tools.

    Wraps :class:`VaultStorage` with MCP-friendly JSON responses and optional
    write protection when the server runs in read-only mode.

    Parameters
    ----------
    storage : VaultStorage
        Active vault for this MCP session.
    read_only : bool
        When ``True``, :meth:`create_entry` is rejected. Write tools should
        also be omitted at registration time in :mod:`stashpad.mcp.server`.
    """

    storage: VaultStorage
    read_only: bool = False

    def _reject_if_read_only(self) -> None:
        """Raise when a write is attempted in read-only mode."""
        if self.read_only:
            msg = "MCP server is running in read-only mode; stash_add is disabled."
            raise ValidationError(msg)

    def search_entries(
        self,
        query: str,
        *,
        limit: int = DEFAULT_SEARCH_LIMIT,
        exact: bool = False,
    ) -> dict[str, Any]:
        """Search entries by title, content, URL, or tags.

        Parameters
        ----------
        query : str
            Search text (fuzzy by default).
        limit : int
            Maximum number of results.
        exact : bool
            When ``True``, disable fuzzy subsequence matching.

        Returns
        -------
        dict
            ``{"entries": [...], "count": N}``
        """

        def _search() -> list[Entry]:
            search_query = SearchQuery(query=query, limit=limit, fuzzy=not exact)
            return self.storage.search(search_query)

        entries = run_vault_operation(_search)
        return format_entry_list_response(entries)

    def list_filtered_entries(
        self,
        *,
        tags: list[str] | None = None,
        kind: str | None = None,
        pinned: bool | None = None,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: str = SortOrder.NEWEST.value,
    ) -> dict[str, Any]:
        """List entries matching optional filters.

        Tag filters use AND semantics (entry must have every listed tag),
        matching ``stash entry list``.

        Parameters
        ----------
        tags : list of str, optional
            Tags that must all be present on each entry.
        kind : str, optional
            Filter by entry kind.
        pinned : bool, optional
            When set, filter by pin state.
        limit : int
            Maximum number of results.
        sort : str
            Sort order: ``newest``, ``oldest``, or ``title``.

        Returns
        -------
        dict
            ``{"entries": [...], "count": N}``
        """

        def _list() -> list[Entry]:
            entry_filter = EntryFilter(
                tags=tags or None,
                kind=parse_entry_kind(kind),
                pinned=pinned,
                limit=limit,
                sort=parse_list_sort_order(sort),
            )
            return self.storage.list_entries(entry_filter)

        entries = run_vault_operation(_list)
        return format_entry_list_response(entries)

    def fetch_entry(self, entry_id: str) -> dict[str, Any]:
        """Fetch one entry by UUID without updating ``opened_at``.

        Unlike ``stash entry show``, this is a pure read for assistant lookups.

        Parameters
        ----------
        entry_id : str
            Entry UUID.

        Returns
        -------
        dict
            ``{"entry": {...}}``
        """

        def _fetch() -> Entry:
            return self.storage.get_entry(parse_entry_uuid(entry_id))

        entry = run_vault_operation(_fetch)
        return format_single_entry_response(entry)

    def create_entry(
        self,
        title: str,
        *,
        content: str = "",
        url: str | None = None,
        tags: list[str] | None = None,
        kind: str | None = None,
        pinned: bool = False,
    ) -> dict[str, Any]:
        """Create a vault entry from assistant context.

        Applies the same kind inference as ``stash entry add``.

        Parameters
        ----------
        title : str
            Entry title.
        content : str
            Body text (command, snippet, or note).
        url : str, optional
            Related http(s) URL.
        tags : list of str, optional
            Entry tags.
        kind : str, optional
            Entry kind; inferred from content when omitted.
        pinned : bool
            Pin the entry for ``stash pins``.

        Returns
        -------
        dict
            ``{"entry": {...}}`` for the created entry.

        Raises
        ------
        ValidationError
            In read-only mode or when input fails validation.
        """
        self._reject_if_read_only()

        def _create() -> Entry:
            explicit_kind = parse_entry_kind(kind)
            normalized_content, normalized_url, resolved_kind = normalize_new_entry(
                content=content,
                url=url,
                kind=explicit_kind,
            )
            payload = EntryCreate(
                title=title,
                content=normalized_content,
                url=normalized_url,
                tags=tags or [],
                pinned=pinned,
                kind=resolved_kind,
            )
            return self.storage.add_entry(payload)

        entry = run_vault_operation(_create)
        return format_single_entry_response(entry)
