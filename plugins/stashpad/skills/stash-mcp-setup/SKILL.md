---
name: stash-mcp-setup
description: |
  Connect a Stashpad vault to Cursor or Claude Desktop via MCP.
  Use when the user wants AI assistant access to their stash, configure stash mcp serve,
  set up MCP in Cursor, Claude Desktop, read-only vs write mode, or troubleshoot MCP tools.
---

# Stashpad MCP Setup

Connect the vault to AI assistants over stdio MCP. Full reference: `docs/mcp.md`.

## Prerequisites

```bash
python3 --version    # MCP requires Python 3.10+
which stash
stash --version
stash config path  # note this path
stash init         # if vault not initialized
```

Install MCP extra if needed:

```bash
pip install "stashpad[mcp]"
# or from source: poetry install -E mcp
```

## Step 1: Choose mode

| Mode | Flag | Tools |
|------|------|-------|
| Read-only (recommended) | `--read-only` | `stash_search`, `stash_list`, `stash_get` |
| Read/write | *(omit flag)* | Above + `stash_add` |

Default to read-only unless the user explicitly wants the assistant to save entries.

## Step 2: Cursor configuration

Edit **Cursor Settings → MCP** or `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "stashpad": {
      "command": "stash",
      "args": ["mcp", "serve", "--read-only"],
      "env": {
        "STASH_DATA_DIR": "/Users/you/.config/stash"
      }
    }
  }
}
```

Replace `STASH_DATA_DIR` with output from `stash config path` (directory containing `vault.json`, not the file itself).

Restart Cursor or reload MCP servers after saving.

### Write mode (optional)

Remove `--read-only` from `args` to enable `stash_add`:

```json
"args": ["mcp", "serve"]
```

## Step 3: Claude Desktop configuration

Add the same block to:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Restart Claude Desktop.

## Step 4: Verify connection

Ask the assistant naturally:

- "Find my kubectl deploy snippet" → should call `stash_search`
- "List pinned devops entries" → should call `stash_list`
- "Show entry `<uuid>`" → should call `stash_get`

Or test CLI directly:

```bash
STASH_DATA_DIR=/path/to/vault stash mcp serve --read-only
```

## Vault selection

Resolution order (same as CLI):

1. `STASH_DATA_DIR` in MCP `env` block (recommended)
2. Default `~/.config/stash`

Alternative via args:

```json
"args": ["--config-dir", "/path/to/vault", "mcp", "serve", "--read-only"]
```

Prefer `STASH_DATA_DIR` in `env` for clarity.

## MCP tool reference

### stash_search

Fuzzy search. Params: `query` (required), `limit`, `exact`.

### stash_list

Filtered list. Params: `tags`, `kind`, `pinned`, `limit`, `sort`.

### stash_get

Fetch by UUID. Params: `entry_id`. Does not update `opened_at`.

### stash_add (write mode only)

Create entry. Params: `title`, `content`, `url`, `tags`, `kind`, `pinned`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `MCP not installed` | `pip install "stashpad[mcp]"` or `poetry install -E mcp` |
| `MCP requires Python 3.10` | Use Python 3.10+ for the `stash` binary |
| `Vault not initialized` | `stash init` in configured `STASH_DATA_DIR` |
| Tools not appearing | Verify `which stash`; restart MCP client; check MCP logs |
| Wrong vault | Set `STASH_DATA_DIR` to match `stash config path` |
| Write fails in read-only | Remove `--read-only` from args |

## Related

- Agent skills install: `docs/agent-skills.md`
- CLI fallback when MCP unavailable: **stash-search**, **stash-capture**
