# Stashpad documentation

Reference documentation for **Stashpad** — a personal developer reference manager (`stash` CLI).

| Guide | Description |
|-------|-------------|
| [Getting started](getting-started.md) | Install, initialize a vault, and run your first commands |
| [CLI reference](cli-reference.md) | All commands, flags, and aliases |
| [Configuration](configuration.md) | Environment variables, vault location, and settings |
| [Data model](data-model.md) | Vault file format, entries, tags, import/export |
| [Development](development.md) | Running tests, linting, and project layout |

## Quick links

- Runnable examples: [`examples/`](../examples/README.md)
- Main project README: [`README.md`](../README.md)

## Typical workflow

```bash
stash init --name my-vault
stash entry add "Docker prune" "docker system prune -af" --tag devops
stash entry list --tag devops
stash search "prune"
stash export json ./backup.json
```

Use `--json` on any command for machine-readable output. See [CLI reference](cli-reference.md#global-options) for global flags.
