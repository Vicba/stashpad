# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Renamed PyPI package from `stash-cli` to `stashpad` (CLI command remains `stash`)

### Removed

- REST API (`api.py`), FastAPI/uvicorn/gunicorn dependencies, and `poe api` task — Stash is CLI-only

## [0.1.0] - 2025-06-14

Initial release of **Stash CLI** — a personal developer reference manager.

### Added

- **CLI** (`stash`) — save and retrieve developer references (commands, snippets, URLs, notes)
- Commands: `init`, `entry` (add/list/show/edit/remove), `search`, `tags`, `export`, `import`, `open`, `config`
- Global flags: `--verbose`, `--json`, `--config-dir`, `--version`; aliases `entry ls` and `entry rm`
- **JSON vault storage** at `~/.config/stash/vault.json` (override via `STASH_DATA_DIR`)
- **Pydantic** domain models and schemas (`Entry`, `EntryCreate`, `EntryUpdate`, `EntryFilter`, `SearchQuery`, `ImportPayload`)
- **Examples** — scripts, sample data, and recipes in `examples/`
- **GitHub Actions** CI and issue templates (bug report, feature request)
- Rich terminal output, shell autocompletion, atomic vault writes
- NumPy-style docstrings and doctest coverage on core modules

[Unreleased]: https://github.com/Vicba/stash-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Vicba/stash-cli/releases/tag/v0.1.0
