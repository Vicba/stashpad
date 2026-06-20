# Agent skills

Stashpad ships an agent skills plugin that teaches AI assistants how to help users set up, capture, search, back up, and connect their vault via MCP.

Skills follow the [agentskills.io](https://agentskills.io) spec (`SKILL.md` + YAML frontmatter). The MCP server gives agents **tools**; skills teach **when and how** to use CLI + MCP together.

**MCP is the main AI integration** — skills are optional workflow guidance on top. See [MCP integration](mcp.md) for vault access in Cursor and Claude Desktop.

## Plugin overview

One plugin (`stashpad`) with six skills:

| Skill | Use when… |
|-------|-----------|
| **stashpad** | General Stashpad questions — routes to the right workflow |
| **stash-setup** | Install, init vault, configure `STASH_DATA_DIR` |
| **stash-capture** | Save commands, URLs, snippets with tags |
| **stash-search** | Find, pick, copy, or run saved entries |
| **stash-backup** | Export, import, migrate between machines |
| **stash-mcp-setup** | Connect vault to Cursor or Claude Desktop |

Source: [`plugins/stashpad/`](../plugins/stashpad/)

## Claude Code vs Claude Desktop

| Client | Skills plugin | MCP (vault search) |
|--------|---------------|-------------------|
| **Claude Code** (terminal) | Yes — `claude plugin install stashpad@stashpad` | Optional — add MCP config |
| **Claude Desktop** (app) | No — skills do not install here | Yes — configure `claude_desktop_config.json` |

Claude Desktop users should follow [MCP integration](mcp.md) only. Claude Code users can install the plugin for workflow skills and optionally add MCP for live vault access.

## Prerequisites

Install the CLI first (skills do not replace `stash`):

```bash
pip install stashpad
# optional, for MCP vault access:
pip install "stashpad[mcp]"
stash init --name my-vault
```

## Install skills

`install.sh` ships in the **GitHub repo**, not on PyPI. If you only `pip install stashpad`, clone the repo to run the installer — or use the Claude Code marketplace (no clone needed).

### Cursor

```bash
git clone https://github.com/Vicba/stashpad.git
cd stashpad
./install.sh install --ide cursor
```

Skills install to `~/.cursor/skills/<skill-name>/`.

**After install:**

1. **Restart Cursor** (or start a new agent chat).
2. Optionally [configure MCP](mcp.md) so the agent can search your vault directly.

Project-local install (optional, for repo contributors testing skills):

```bash
./install.sh install --ide cursor --target .cursor/skills
```

### Claude Code

No clone required after the plugin is on `main`:

```bash
claude plugin marketplace add Vicba/stashpad
claude plugin install stashpad@stashpad
```

Optionally add MCP so the agent can query your vault — see [MCP integration](mcp.md).

### Codex

Requires a repo clone (same as Cursor):

```bash
git clone https://github.com/Vicba/stashpad.git
cd stashpad
./install.sh install --ide codex
```

Skills install to `~/.codex/skills/<skill-name>/`. Restart Codex after install.

### Google Antigravity

```bash
git clone https://github.com/Vicba/stashpad.git
cd stashpad
./install.sh install --ide antigravity
```

Skills install to `~/.gemini/config/plugins/stashpad/skills/<skill-name>/`.

## Install script reference

```bash
./install.sh list                              # list plugins and skills
./install.sh install                           # install all (default: codex)
./install.sh install --ide cursor              # install to Cursor
./install.sh update stashpad --ide cursor      # update installed skills
./install.sh verify --ide codex                # verify installed files
./install.sh uninstall --ide cursor            # remove installed skills
./install.sh --target /tmp/skills install      # custom target dir
```

After `install` or `update`, the script runs `verify` automatically.

## MCP + skills together (recommended)

1. Install Stashpad with MCP extra: `pip install "stashpad[mcp]"`
2. Configure MCP — see [MCP integration](mcp.md)
3. Install agent skills (Cursor/Codex: clone repo + `./install.sh`; Claude Code: plugin install)
4. Restart your AI client

With both connected, agents use MCP tools when available and fall back to `stash` shell commands otherwise.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Skills not appearing | **Restart** Cursor/Codex after install; confirm files in `~/.cursor/skills/` |
| Skill collision error on install | Another plugin owns the skill name — uninstall it or use `--target` |
| Agent doesn't use stash | Install skills; ensure MCP is configured or CLI is on `PATH` |
| `./install.sh` not found | Clone the repo — the script is not included in the PyPI package |
| Claude Desktop has no skills | Expected — use MCP only; see [MCP integration](mcp.md) |
| `./install.sh verify` fails | Re-run `./install.sh install --ide <ide>` |

## See also

- [MCP integration](mcp.md) — MCP server setup and tool reference
- [Getting started](getting-started.md) — vault init and first entries
- [plugins/stashpad/README.md](../plugins/stashpad/README.md) — plugin README
