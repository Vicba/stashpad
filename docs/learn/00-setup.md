# Setup

Covers Typer tutorial sections: [Environment Variables](https://typer.tiangolo.com/tutorial/environment-variables/), [Virtual Environments](https://typer.tiangolo.com/tutorial/virtual-environments/), [Install Typer](https://typer.tiangolo.com/tutorial/install/), [Building a Package](https://typer.tiangolo.com/tutorial/package/).

## Prerequisites

- Python 3.8–3.12
- [Poetry](https://python-poetry.org/docs/#installation)

## Install

```bash
git clone https://github.com/victorbarra/stash-cli.git
cd stash-cli
poetry install
```

## Verify

```bash
poetry run stash --version
poetry run stash --help
```

## Typer dev runner

Without installing the script globally, use the [`typer` command](https://typer.tiangolo.com/tutorial/typer-command/):

```bash
poetry run poe dev -- --help
# equivalent to: poetry run typer stash_cli.cli run --help
```

## Environment variables

Copy `.env.example` to `.env`:

| Variable | Purpose |
|----------|---------|
| `STASH_DATA_DIR` | Override vault directory (default: `~/.config/stash`) |
| `STASH_DEBUG` | Enable debug mode |
| `STASH_MAX_ENTRIES` | Maximum vault size |

Used in: `src/stash_cli/config.py`, `src/stash_cli/cli.py` (global `--config-dir`).

## Docker

```bash
docker compose --profile app up app   # API on :8000
docker compose --profile dev up dev   # dev container
```
