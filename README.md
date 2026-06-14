# Stash CLI

**Stash** is a personal developer reference manager — and a hands-on course for learning [Typer](https://typer.tiangolo.com/) from beginner to advanced.

Save URLs, shell commands, code snippets, and notes. Tag them, search, export, and browse via CLI or REST API. Every command demonstrates a Typer concept from the [official tutorial](https://typer.tiangolo.com/tutorial/).

## How it works

Stash is a **local, searchable cheat sheet** for developers. You save things you look up repeatedly — shell commands, snippets, URLs, notes — and find them again from the terminal or over HTTP.

### Data storage

Everything lives in a single JSON file:

```
~/.config/stash/vault.json    # default location
```

Override with `STASH_DATA_DIR`, `--config-dir`, or a path passed to `stash init`. The file contains:

- **Entries** — title, content, optional URL, tags, priority, timestamps, UUID
- **Tags** — a registry of tag names used in the vault

Example scripts use `examples/.demo-vault/` so they never touch your real vault.

### Two interfaces, one vault

| Interface | Purpose |
|-----------|---------|
| **CLI** (`stash`) | Day-to-day use in the terminal |
| **REST API** | Same data over HTTP (`/entries`, `/search`, `/docs`) |

Both read and write through the same storage layer and Pydantic models — no duplicated business logic.

### Typical workflow

```bash
stash init --name my-vault                         # create vault once
stash entry add "Docker prune" "docker ..." --tag devops
stash entry list --tag devops                    # filter by tag
stash search "prune"                             # full-text search
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
CLI commands  ──┐
                ├──►  storage.py  ──►  vault.json
API (FastAPI) ──┘         ▲
                          │
                    models / schemas (Pydantic)
```

The CLI doubles as a **Typer learning project**: each feature maps to a section of the [Typer tutorial](https://typer.tiangolo.com/tutorial/). See [`docs/learn/`](docs/learn/00-overview.md) for the full curriculum.

## Quick start

```bash
git clone https://github.com/victorbarra/stash-cli.git
cd stash-cli
poetry install

# Initialize your vault
poetry run stash init --name my-vault

# Add a reference
poetry run stash entry add "Docker prune" "docker system prune -af" \
  --tag devops --tag docker --url https://docs.docker.com

# List and search
poetry run stash entry list --tag devops
poetry run stash search "prune"

# JSON output mode
poetry run stash --json entry list
```

## CLI commands

| Command | Description |
|---------|-------------|
| `stash init` | Initialize vault (prompts, env vars, password confirmation) |
| `stash entry add/list/show/edit/remove` | CRUD with UUID, enums, filters, aliases (`ls`, `rm`) |
| `stash search` | Full-text search |
| `stash tags list/add/remove` | Nested subcommands with sub-Typer callback |
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

## REST API

```bash
poetry run poe api --dev
# Open http://localhost:8000/docs
```

Endpoints mirror the CLI: `POST/GET/PATCH/DELETE /entries`, `GET /search`, `GET /tags`, `GET /health`.

## Learn Typer

Start with the guided curriculum:

1. [Setup](docs/learn/00-setup.md) — virtual env, install, dev runner
2. [Overview](docs/learn/00-overview.md) — learning path
3. [Beginner](docs/learn/01-beginner.md) — arguments, options, first commands
4. [Intermediate](docs/learn/02-intermediate.md) — prompts, subcommands, multiple values
5. [Advanced](docs/learn/03-advanced.md) — context, autocompletion, progress, launch
6. [Testing](docs/learn/04-testing.md) — CliRunner patterns
7. [Professional patterns](docs/learn/05-professional-patterns.md) — exit codes, XDG dirs, JSON mode
8. [Click internals](docs/learn/06-click-internals.md) — vendored Click
9. [Command map](docs/learn/COMMAND_MAP.md) — every Typer doc section → source file

## Development

```bash
poetry run poe test      # run tests
poetry run poe lint      # lint
poetry run poe dev       # typer dev runner
poetry run poe api --dev # start API
```

## Project structure

```
src/stash_cli/
  cli.py              # root app + global callback
  context.py          # shared AppContext
  models.py           # Entry, Vault, enums
  storage.py          # JSON persistence (~/.config/stash/)
  commands/           # one module per command group
  api.py              # FastAPI mirror
docs/learn/           # Typer learning curriculum
tests/                # CliRunner + API tests
```

## License

MIT
