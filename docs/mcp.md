# MCP integration

Stashpad can run as an [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) server so AI assistants in **Cursor**, **Claude Desktop**, and other MCP clients can search and read your personal vault while you code.

The client spawns `stash mcp serve` as a background process and talks to it over **stdio** (stdin/stdout). You do not run the server manually in a terminal.

## Requirements

- **Python 3.10+** (MCP SDK requirement; the rest of Stashpad still supports 3.8+)
- Stashpad installed with the optional MCP extra
- An initialized vault (`stash init`)

```bash
# From source
poetry install -E mcp

# When published
pip install "stashpad[mcp]"
```

Confirm your vault path:

```bash
stash config path
```

## Quick setup (Cursor)

1. Open **Cursor Settings → MCP** (or edit `~/.cursor/mcp.json`).
2. Add a server entry:

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

3. Replace `STASH_DATA_DIR` with the path from `stash config path`.
4. Ensure `stash` is on your `PATH` (`which stash`).
5. Restart Cursor or reload MCP servers.

### Read-only vs write mode

| Mode | Flag | Tools available |
|------|------|-----------------|
| Read-only (recommended) | `--read-only` | `stash_search`, `stash_list`, `stash_get` |
| Read/write | *(omit flag)* | Above + `stash_add` |

Read-only mode is safer for everyday coding: the assistant can look up your snippets but cannot create entries. Remove `--read-only` when you want the assistant to save commands or notes from chat context.

## Claude Desktop

Add the same JSON block to your Claude Desktop MCP config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

## Vault selection

The MCP server uses the same vault resolution as the CLI:

1. `STASH_DATA_DIR` in the MCP `env` block (recommended)
2. Default `~/.config/stash` (or `$XDG_CONFIG_HOME/stash`)

You can also pass `--config-dir` in `args`, but setting `STASH_DATA_DIR` in `env` is clearer for MCP clients.

```json
"args": ["--config-dir", "/path/to/vault", "mcp", "serve", "--read-only"]
```

## MCP tools

All tools return JSON. Entry objects match `stash --json entry list` output.

### `stash_search`

Fuzzy search by title, content, URL, or tags.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search text |
| `limit` | integer | 20 | Maximum results |
| `exact` | boolean | false | Disable fuzzy matching |

**Returns:** `{"entries": [...], "count": N}`

### `stash_list`

List entries with optional filters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tags` | list of strings | null | Entries must have **all** listed tags |
| `kind` | string | null | `command`, `url`, `snippet`, or `note` |
| `pinned` | boolean | null | Filter pinned entries |
| `limit` | integer | 50 | Maximum results |
| `sort` | string | `newest` | `newest`, `oldest`, or `title` |

**Returns:** `{"entries": [...], "count": N}`

### `stash_get`

Fetch one entry by UUID. Does **not** update `opened_at` (pure read).

| Parameter | Type | Description |
|-----------|------|-------------|
| `entry_id` | string | Entry UUID |

**Returns:** `{"entry": {...}}`

### `stash_add`

Create a new entry. **Not registered in read-only mode.**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | string | required | Entry title |
| `content` | string | `""` | Body text |
| `url` | string | null | Optional http(s) URL |
| `tags` | list of strings | null | Tags |
| `kind` | string | null | Inferred from content when omitted |
| `pinned` | boolean | false | Pin the entry |

**Returns:** `{"entry": {...}}`

## Example assistant usage

Once connected, you can ask naturally:

- “Find my kubectl deploy snippet” → `stash_search`
- “List pinned devops entries” → `stash_list`
- “Show entry `550e8400-...`” → `stash_get`
- “Save this command to my vault” → `stash_add` *(write mode only)*

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `MCP not installed` | Run `poetry install -E mcp` or `pip install "stashpad[mcp]"` |
| `MCP requires Python 3.10` | Upgrade Python or use a 3.10+ virtualenv for `stash` |
| `Vault not initialized` | Run `stash init` in the configured `STASH_DATA_DIR` |
| Tools not appearing | Verify `which stash`; restart the MCP client; check MCP logs |
| Wrong vault | Set `STASH_DATA_DIR` in MCP `env` to match `stash config path` |

## CLI reference

```bash
stash mcp serve [--read-only]
stash --config-dir /path/to/vault mcp serve
```

See also [CLI reference — stash mcp](cli-reference.md#stash-mcp).
