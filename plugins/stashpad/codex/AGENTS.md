# Stashpad agent skills

This plugin teaches agents how to help users manage a local Stashpad vault (`stash` CLI).

## When to use

- User wants to save, find, or run shell commands, URLs, or snippets
- User needs vault setup, backup, or MCP configuration
- User mentions "stash", "Stashpad", or a personal snippet vault

## Skill routing

| Intent | Skill |
|--------|-------|
| First-time setup, vault path, init | stash-setup |
| Save command/URL/snippet from chat | stash-capture |
| Find, copy, or run a saved entry | stash-search |
| Backup, restore, migrate vault | stash-backup |
| Connect to Cursor / Claude Desktop | stash-mcp-setup |
| General / unclear | stashpad (router) |

## MCP-first rule

If `stash_search`, `stash_list`, `stash_get`, or `stash_add` MCP tools are available, use them. Fall back to `stash` shell commands when MCP is not connected.

## Safety

- Recommend read-only MCP (`--read-only`) by default
- Confirm before `stash entry run` or write-mode `stash_add`
- Never overwrite a user's personal vault without explicit consent

## Reference docs

- `docs/getting-started.md` — install and init
- `docs/cli-reference.md` — all commands and flags
- `docs/mcp.md` — MCP tools and client config
- `llms.txt` — compact project overview
