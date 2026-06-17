"""MCP server integration for Stashpad.

Expose the personal vault to AI assistants via ``stash mcp serve``.
See ``docs/mcp.md`` for Cursor and Claude Desktop setup.
"""

from stashpad.mcp.server import (
    READ_TOOLS,
    TOOL_ADD,
    TOOL_GET,
    TOOL_LIST,
    TOOL_SEARCH,
    WRITE_TOOLS,
    build_mcp_server,
    list_registered_tool_names,
    run_mcp_server,
)
from stashpad.mcp.service import VaultMcpService

__all__ = [
    "READ_TOOLS",
    "TOOL_ADD",
    "TOOL_GET",
    "TOOL_LIST",
    "TOOL_SEARCH",
    "WRITE_TOOLS",
    "VaultMcpService",
    "build_mcp_server",
    "list_registered_tool_names",
    "run_mcp_server",
]
