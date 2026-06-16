"""FastMCP server wiring for Stashpad vault tools.

Registers MCP tool names that match the issue spec:

- ``stash_search`` — fuzzy vault search
- ``stash_list``   — filtered listing
- ``stash_get``    — fetch one entry (pure read)
- ``stash_add``    — create entry (write mode only)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from stashpad.constants import DEFAULT_LIST_LIMIT, DEFAULT_SEARCH_LIMIT
from stashpad.mcp.service import VaultMcpService

if TYPE_CHECKING:
    from stashpad.storage import VaultStorage

MCP_SERVER_NAME = "stashpad"

# Tool names exposed to MCP clients (stable public contract).
TOOL_SEARCH = "stash_search"
TOOL_LIST = "stash_list"
TOOL_GET = "stash_get"
TOOL_ADD = "stash_add"

READ_TOOLS = (TOOL_SEARCH, TOOL_LIST, TOOL_GET)
WRITE_TOOLS = (TOOL_ADD,)


def list_registered_tool_names(server: Any) -> set[str]:
    """Return tool names registered on a FastMCP server instance.

    Parameters
    ----------
    server : FastMCP
        Server returned by :func:`build_mcp_server`.

    Returns
    -------
    set of str
        Registered MCP tool names.
    """
    return set(server._tool_manager._tools)


def _assistant_instructions(*, allow_writes: bool) -> str:
    """Build usage hints shown to the connected AI assistant."""
    instructions = (
        "Search and read a personal developer vault (commands, URLs, snippets, notes). "
        f"Use {TOOL_SEARCH} for fuzzy lookup, {TOOL_LIST} for filters, "
        f"and {TOOL_GET} for one entry by UUID."
    )
    if allow_writes:
        instructions += f" Use {TOOL_ADD} to save new entries from assistant context."
    return instructions


def _register_read_tools(mcp_server: Any, vault_service: VaultMcpService) -> None:
    """Register search, list, and get tools (always available)."""

    @mcp_server.tool(name=TOOL_SEARCH)
    def stash_search(
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        exact: bool = False,
    ) -> dict[str, Any]:
        """Search vault entries by title, content, URL, or tags."""
        return vault_service.search_entries(query, limit=limit, exact=exact)

    @mcp_server.tool(name=TOOL_LIST)
    def stash_list(
        tags: list[str] | None = None,
        kind: str | None = None,
        pinned: bool | None = None,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: str = "newest",
    ) -> dict[str, Any]:
        """List vault entries with optional tag, kind, and pin filters."""
        return vault_service.list_filtered_entries(
            tags=tags,
            kind=kind,
            pinned=pinned,
            limit=limit,
            sort=sort,
        )

    @mcp_server.tool(name=TOOL_GET)
    def stash_get(entry_id: str) -> dict[str, Any]:
        """Fetch one vault entry by UUID without changing opened_at."""
        return vault_service.fetch_entry(entry_id)


def _register_write_tools(mcp_server: Any, vault_service: VaultMcpService) -> None:
    """Register stash_add (omitted in read-only mode)."""

    @mcp_server.tool(name=TOOL_ADD)
    def stash_add(
        title: str,
        content: str = "",
        url: str | None = None,
        tags: list[str] | None = None,
        kind: str | None = None,
        pinned: bool = False,
    ) -> dict[str, Any]:
        """Create a new vault entry from assistant context."""
        return vault_service.create_entry(
            title,
            content=content,
            url=url,
            tags=tags,
            kind=kind,
            pinned=pinned,
        )


def build_mcp_server(vault_service: VaultMcpService) -> Any:
    """Create a FastMCP server with Stashpad tools registered.

    Parameters
    ----------
    vault_service : VaultMcpService
        Vault service bound to the active storage session.

    Returns
    -------
    FastMCP
        Configured server; call ``run(transport="stdio")`` to start.
    """
    from mcp.server.fastmcp import FastMCP

    allow_writes = not vault_service.read_only
    mcp_server = FastMCP(
        MCP_SERVER_NAME,
        instructions=_assistant_instructions(allow_writes=allow_writes),
    )

    _register_read_tools(mcp_server, vault_service)
    if allow_writes:
        _register_write_tools(mcp_server, vault_service)

    return mcp_server


def run_mcp_server(storage: VaultStorage, *, read_only: bool = False) -> None:
    """Start the Stashpad MCP server on stdio until the client disconnects.

    Parameters
    ----------
    storage : VaultStorage
        Initialized vault storage for this session.
    read_only : bool
        When ``True``, only read tools are registered.
    """
    vault_service = VaultMcpService(storage, read_only=read_only)
    mcp_server = build_mcp_server(vault_service)
    mcp_server.run(transport="stdio")
