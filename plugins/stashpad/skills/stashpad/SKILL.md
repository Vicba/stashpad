---
name: stashpad
description: |
  Router for Stashpad — local developer reference vault (stash CLI).
  Use when the user asks about Stashpad, stash, saving/finding snippets,
  vault setup, backup, or MCP integration. Detects intent and delegates
  to stash-setup, stash-capture, stash-search, stash-backup, or stash-mcp-setup.
---

# Stashpad

Stashpad is a local CLI vault for shell commands, URLs, snippets, and notes (`pip install stashpad`, command `stash`). Data lives in `vault.json` on disk — no cloud sync.

## Step 1: Check MCP availability

If these MCP tools are in your tool list, prefer them over shell commands:

- `stash_search` — fuzzy search
- `stash_list` — filtered listing
- `stash_get` — fetch one entry by UUID
- `stash_add` — create entry (write mode only)

If MCP tools are unavailable, use shell `stash` commands.

## Step 2: Route by intent

| User intent | Load skill |
|-------------|------------|
| Install, init, vault path, `STASH_DATA_DIR` | stash-setup |
| Save command/URL/snippet from chat or clipboard | stash-capture |
| Find, list, copy, or run a saved entry | stash-search |
| Backup, restore, migrate, dry-run import | stash-backup |
| Connect vault to Cursor or Claude Desktop | stash-mcp-setup |

If intent is ambiguous, ask one clarifying question:

> Are you trying to **set up** Stashpad, **save** something, **find** an entry, **back up** your vault, or **connect it to an AI assistant**?

Then follow the matching skill workflow.

## Step 3: Safety defaults

- Recommend read-only MCP (`stash mcp serve --read-only`) unless the user wants write access
- Confirm before `stash entry run` (executes shell commands)
- Confirm before overwriting vaults (`stash init --force`, imports)
- Never touch the user's personal vault without explicit consent

## Reference

- Project overview: `llms.txt`
- Full CLI: `docs/cli-reference.md`
- MCP tools: `docs/mcp.md`
