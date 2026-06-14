# Development

Guide for contributors and local development of Stashpad.

## Setup

```bash
git clone https://github.com/Vicba/stash-cli.git
cd stash-cli
poetry install
```

## Common tasks

| Task | Command |
|------|---------|
| Run tests | `poetry run poe test` |
| Lint | `poetry run poe lint` |
| CLI dev runner | `poetry run poe dev -- --help` |

Run the CLI without a global install:

```bash
poetry run stash --help
poetry run typer stash_cli.cli run --help   # equivalent to poe dev
```

## Project structure

```
src/stash_cli/
  cli.py              # Root Typer app and global callback
  context.py          # Shared AppContext (storage, flags)
  config.py           # Settings and XDG data directory
  models.py           # Entry, Vault, enums
  schemas.py          # Pydantic request/filter schemas
  storage.py          # JSON persistence (vault.json)
  output.py           # Table/JSON formatting
  commands/           # One module per command group
    entry.py          # entry add/list/show/edit/remove
    init.py
    search.py
    tags.py
    export.py
    import_cmd.py
    open_cmd.py
    config_cmd.py
tests/                # pytest (CliRunner)
examples/             # Runnable scripts and sample data
docs/                 # Reference documentation
```

## Architecture

```
CLI commands  ──►  storage.py  ──►  vault.json
                        ▲
                        │
                  models / schemas (Pydantic)
```

- **CLI** — Typer commands in `commands/`; global options in `cli.py` callback
- **Storage** — Atomic JSON read/write; no database
- **Validation** — Pydantic models in `models.py` and `schemas.py`

## Testing

Tests use `pytest` with `typer.testing.CliRunner` for CLI commands.

```bash
poetry run pytest
poetry run pytest tests/test_cli.py -v
poetry run pytest -k "entry" -v
```

Key test modules:

| File | Coverage |
|------|----------|
| `tests/test_cli.py` | CLI commands and global flags |
| `tests/test_storage.py` | Vault persistence |
| `tests/test_models.py` | Pydantic validation |

## Linting and formatting

```bash
poetry run poe lint    # ruff check
poetry run ruff check src tests
poetry run mypy src    # if run separately
```

Pre-commit hooks are configured in `.pre-commit-config.yaml`:

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## Using an isolated vault for development

Avoid touching your personal vault during experiments:

```bash
export STASH_DATA_DIR=/tmp/stash-dev
stash init --name dev --force
stash entry add "Test" "content" --tag dev
```

Example scripts use `examples/.demo-vault/` the same way.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to `main`:

- `pytest` on Python 3.11 and 3.12
- `ruff check` on `src` and `tests`
- CLI smoke test (`stash --version`, `stash --help`, getting-started script)

## Release

Version is managed in `pyproject.toml` and tracked in `CHANGELOG.md`. Commitizen is configured for conventional releases:

```bash
poetry run cz bump
```

## Documentation

User-facing reference docs live in [`docs/`](README.md). When adding commands, update:

- `docs/cli-reference.md`
- `README.md` command summary (if user-visible)
- Tests in `tests/`
