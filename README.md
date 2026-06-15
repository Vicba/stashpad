# Stashpad

**Stashpad** is a personal developer reference manager (`stash` on the command line).

Save URLs, shell commands, code snippets, and notes. Tag them, search, export, and browse from the terminal.

Full reference: [`docs/`](docs/README.md)

## How it works

Stashpad is a **local, searchable cheat sheet** for developers. You save things you look up repeatedly — shell commands, snippets, URLs, notes — and find them again from the terminal.

### Data storage

Everything lives in a single JSON file:

```
~/.config/stash/vault.json    # default location
```

Override with `STASH_DATA_DIR`, `--config-dir`, or a path passed to `stash init`. The file contains:

- **Entries** — title, content, optional URL, tags, priority, timestamps, UUID
- **Tags** — a registry of tag names used in the vault

Example scripts use `examples/.demo-vault/` so they never touch your real vault.

### Typical workflow

```bash
stash init --name my-vault                         # create vault once
stash entry add "Docker prune" "docker ..." --tag devops
stash entry list --tag devops                    # filter by tag
stash search "prune"                             # full-text search
stash entry copy <id> --first-line               # copy command to clipboard
stash entry run <id>                             # run with confirmation
stash export json ./backup.json                  # backup
stash import --from-file ./backup.json           # restore
```

Useful global flags: `--json` (scripting), `--verbose`, `--config-dir` (alternate vault).

### Validation with Pydantic

Input is validated before it hits disk:

| Schema | Used for |
|--------|----------|
| `EntryCreate` | New entries (title, URL, tags normalized) |
| `EntryUpdate` | Partial edits |
| `EntryFilter` | List/search filters |
| `ImportPayload` | JSON import files |

Invalid URLs, empty titles, or malformed import files fail early with clear errors.

### Architecture

```
CLI commands  ──►  storage.py  ──►  vault.json
                        ▲
                        │
                  models / schemas (Pydantic)
```

## Quick start

```bash
pip install stashpad
# or: pipx install stashpad

stash init --name my-vault

stash entry add "Docker prune" "docker system prune -af" \
  --tag devops --tag docker --url https://docs.docker.com

stash entry list --tag devops
stash search "prune"
stash --json entry list
```

From source:

```bash
git clone https://github.com/Vicba/stash-cli.git
cd stash-cli
poetry install
poetry run stash init --name my-vault
```

## CLI commands

| Command | Description |
|---------|-------------|
| `stash init` | Initialize vault (prompts, env vars) |
| `stash entry add/list/show/edit/remove/copy/run` | CRUD with UUID, enums, filters, aliases (`ls`, `rm`) |
| `stash search` | Full-text search |
| `stash tags list/add/remove` | Nested subcommands |
| `stash export json/markdown` | Export with Path types and progress bars |
| `stash import` | Import from JSON files |
| `stash open` | Open entry URL in browser |
| `stash config show/set/path` | Configuration management |

Global flags: `--verbose`, `--json`, `--config-dir`, `--version`

Run `poetry run stash --help` for full usage.

## Examples

Runnable walkthroughs and sample data live in [`examples/`](examples/README.md):

```bash
./examples/scripts/01-getting-started.sh
./examples/scripts/04-import-export.sh
```

## Development

```bash
poetry run poe test      # run tests
poetry run poe lint      # lint
poetry run poe dev       # dev runner
```

## Project structure

```
src/stash_cli/
  cli.py              # root app + global callback
  context.py          # shared AppContext
  models.py           # Entry, Vault, enums
  storage.py          # JSON persistence (~/.config/stash/)
  commands/           # one module per command group
docs/                 # Reference documentation
tests/                # CLI tests
```

## License

MIT
