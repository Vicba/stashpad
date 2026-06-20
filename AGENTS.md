# Stashpad — agent guidance

Stashpad is a local CLI vault for shell commands, URLs, snippets, and notes. Package: `stashpad`, command: `stash`.

## For agents helping users

Install the **stashpad** skills plugin so you know when and how to use the CLI and MCP tools:

```bash
./install.sh install --ide cursor    # Cursor (requires repo clone)
./install.sh install --ide codex     # Codex (requires repo clone)
claude plugin install stashpad@stashpad   # Claude Code (after marketplace add)
```

`install.sh` is in the repo, not on PyPI. Claude Desktop does not install skills — use MCP only. See [docs/agent-skills.md](docs/agent-skills.md) for full install instructions.

## Skill routing

| User intent | Skill |
|-------------|-------|
| Setup, init, vault path | stash-setup |
| Save command/URL/snippet | stash-capture |
| Find, copy, run entry | stash-search |
| Backup, restore, migrate | stash-backup |
| Connect to Cursor / Claude Desktop | stash-mcp-setup |
| General / unclear | stashpad (router) |

## MCP-first

When Stashpad MCP tools are available (`stash_search`, `stash_list`, `stash_get`, `stash_add`), prefer them over shell commands. Default to read-only MCP unless the user wants write access.

## Key docs

| Doc | Purpose |
|-----|---------|
| [llms.txt](llms.txt) | Compact project overview |
| [docs/getting-started.md](docs/getting-started.md) | Install and first entries |
| [docs/cli-reference.md](docs/cli-reference.md) | All commands and flags |
| [docs/mcp.md](docs/mcp.md) | MCP setup and tool reference |
| [docs/agent-skills.md](docs/agent-skills.md) | Skills plugin install guide |
| [docs/devcontainer.md](docs/devcontainer.md) | Contributor dev container |

## Safety

- Confirm before `stash entry run` (executes shell commands)
- Confirm before vault overwrite (`stash init --force`, imports)
- Recommend `--read-only` for MCP in everyday use

## Repository layout

```
src/stashpad/       # Python CLI, TUI, MCP server
plugins/stashpad/   # Agent skills plugin (6 skills)
docs/               # User and agent documentation
install.sh          # Install skills to Cursor, Codex, Antigravity
```
