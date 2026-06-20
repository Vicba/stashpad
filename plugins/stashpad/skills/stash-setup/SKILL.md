---
name: stash-setup
description: |
  Set up Stashpad (stash CLI) — install, initialize vault, configure STASH_DATA_DIR
  and vault paths. Use when the user is new to stash, gets "vault not initialized",
  needs a separate dev/sandbox vault, or asks where their data is stored.
---

# Stashpad Setup

Follow these steps in order. See `docs/getting-started.md` and `docs/configuration.md` for full reference.

## Step 1: Verify installation

```bash
which stash
stash --version
stash --help
```

If `stash` is not found:

```bash
pip install stashpad
# or: pipx install stashpad
```

From source (repo checkout):

```bash
poetry install
poetry run stash --version
```

## Step 2: Check vault status

```bash
stash config path
```

Expected default: `~/.config/stash` (vault file: `vault.json` inside that directory)

If the vault does not exist, initialize:

```bash
stash init --name my-vault
```

Re-initialize an existing vault only with explicit user consent:

```bash
stash init --name my-vault --force
```

## Step 3: Configure vault location (optional)

Priority order (highest first):

1. `--config-dir` CLI flag (one-off)
2. `STASH_DATA_DIR` environment variable
3. `$XDG_CONFIG_HOME/stash`
4. `~/.config/stash`

Examples:

```bash
# Persistent custom location
export STASH_DATA_DIR=/path/to/my-vault
stash init --name demo

# One-off
stash --config-dir /tmp/stash-sandbox init --name sandbox --force
```

For isolated testing (never touches personal vault):

```bash
STASH_DATA_DIR=/tmp/stash-sandbox stash init --name sandbox --force
```

## Step 4: Verify with a test entry

```bash
stash entry add "Setup test" "echo hello" --tag test
stash entry list --tag test
stash search "setup test"
```

## Step 5: Optional extras

| Feature | Install | Verify |
|---------|---------|--------|
| TUI browse | `pip install "stashpad[tui]"` | `stash browse` |
| MCP server | `pip install "stashpad[mcp]"` (Python 3.10+) | `stash mcp serve --help` |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Vault not initialized` | Run `stash init` in the configured `STASH_DATA_DIR` |
| Wrong vault | Set `STASH_DATA_DIR` or use `--config-dir`; confirm with `stash config path` |
| Permission errors | Check directory ownership for `STASH_DATA_DIR` |

## Next steps

- Save entries → use **stash-capture**
- Connect to Cursor → use **stash-mcp-setup**
