# Stashpad plugin

Agent skills that teach AI assistants how to help users work with [Stashpad](https://github.com/Vicba/stashpad) — a local CLI vault for shell commands, URLs, snippets, and notes.

## Skills

| Skill | Purpose |
|-------|---------|
| **stashpad** | Router — detect intent and delegate to the right workflow |
| **stash-setup** | Install, init vault, configure paths |
| **stash-capture** | Save commands, URLs, snippets with tags and priority |
| **stash-search** | Search, pick, pins, copy/run entries |
| **stash-backup** | Export, import, migrate between machines |
| **stash-mcp-setup** | Connect vault to Cursor or Claude Desktop via MCP |

## Install

### Claude Code

Skills plugin (no repo clone required):

```bash
claude plugin marketplace add Vicba/stashpad
claude plugin install stashpad@stashpad
```

Optionally add MCP for live vault access — see [docs/mcp.md](../../docs/mcp.md).

### Claude Desktop

**MCP only** — the skills plugin does not install in Claude Desktop. Configure MCP in `claude_desktop_config.json`; see [docs/mcp.md](../../docs/mcp.md).

### Cursor, Codex, Antigravity

Requires a repo clone — `install.sh` is not shipped on PyPI:

```bash
git clone https://github.com/Vicba/stashpad.git
cd stashpad
./install.sh install --ide cursor
./install.sh install --ide codex
./install.sh install --ide antigravity
```

After install, **restart** your AI client. Optionally configure MCP — see [docs/agent-skills.md](../../docs/agent-skills.md).

## MCP vs CLI

When Stashpad MCP tools (`stash_search`, `stash_list`, `stash_get`, `stash_add`) are available, skills prefer them. Otherwise they fall back to shell `stash` commands.
