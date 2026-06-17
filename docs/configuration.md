# Configuration

Stash reads settings from environment variables and an optional `.env` file in the project or working directory. All variables use the `STASH_` prefix.

Copy `.env.example` to `.env` to get started:

```bash
cp .env.example .env
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STASH_DATA_DIR` | `~/.config/stash` | Vault storage directory |
| `STASH_DEBUG` | `false` | Enable debug mode |
| `STASH_MAX_ENTRIES` | `10000` | Soft limit for vault size |

Additional settings exist in code (`default_format`, `editor`, etc.) and appear in `stash config show` but are not all overridable via CLI today.

## Vault location

The vault file is always:

```
<data_dir>/vault.json
```

Default data directory resolution:

1. `--config-dir` on the CLI (highest priority for that invocation)
2. `STASH_DATA_DIR` environment variable
3. `$XDG_CONFIG_HOME/stash` if `XDG_CONFIG_HOME` is set
4. `~/.config/stash` otherwise

Initialize a vault in a custom location:

```bash
# One-off via flag
stash --config-dir /tmp/my-vault entry list

# Persistent via environment
export STASH_DATA_DIR=/tmp/my-vault
stash init --name demo

# Or pass directory to init
stash init /tmp/my-vault --name demo
```

Inspect the active path:

```bash
stash config path
```

## MCP (AI assistants)

To expose your vault to Cursor or Claude Desktop, install the MCP extra and configure the client to run `stash mcp serve`. See [MCP integration](mcp.md) for setup, tool reference, and example `mcp.json` configs.

## View current settings

```bash
stash config show
stash --json config show
```

Example output keys: `app_name`, `app_version`, `debug`, `data_dir`, `max_entries`.

## Persisting changes

Use `stash config set` to see how to map a setting to an environment variable:

```bash
stash config set --key debug --value true
# Hint: add STASH_DEBUG=true to your .env file
```

Settings are not written to disk by `config set` — add the suggested line to `.env` or your shell profile.
