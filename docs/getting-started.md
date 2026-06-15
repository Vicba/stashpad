# Getting started

## Prerequisites

- Python 3.8–3.12
- [Poetry](https://python-poetry.org/docs/#installation)

## Install

```bash
pip install stashpad
# or: pipx install stashpad
```

Verify the CLI:

```bash
stash --version
stash --help
```

### Install from source

```bash
git clone https://github.com/Vicba/stash-cli.git
cd stash-cli
poetry install
```

After a source install, use `poetry run stash` or activate the Poetry shell.

## Initialize a vault

Stash stores data in a local JSON vault. Create one with:

```bash
poetry run stash init --name my-vault
```

By default the vault lives at `~/.config/stash/vault.json`. You can override the directory with `--config-dir`, the `STASH_DATA_DIR` environment variable, or a path argument to `stash init`. See [Configuration](configuration.md).

Re-initialize an existing vault with `--force`:

```bash
poetry run stash init --name my-vault --force
```

## Add your first entries

```bash
poetry run stash entry add "Docker prune" "docker system prune -af" \
  --tag devops --tag docker \
  --url https://docs.docker.com/config/pruning/ \
  --priority high

poetry run stash entry add "Git undo" "git reset --soft HEAD~1" --tag git
```

Quick capture from clipboard, stdin, or the `stash add` alias:

```bash
poetry run stash add "Clipboard snippet" --clipboard
git log --oneline -5 | poetry run stash add "Recent commits" -
poetry run stash add "Quick note" "echo hello"   # top-level alias
```

Use `--interactive` / `-i` to be prompted for fields:

```bash
poetry run stash entry add "" "" --interactive
```

## List and search

```bash
# Filter by tag or priority
poetry run stash entry list --tag devops
poetry run stash entry list --priority high

# Full-text search across title, content, URL, and tags
poetry run stash search "docker"
poetry run stash search prn              # fuzzy: matches "Docker prune", etc.
poetry run stash search prn --exact      # disable fuzzy matching

# Pinned favorites
poetry run stash pins
poetry run stash entry list --pinned

# Interactive picker (install fzf for best experience)
poetry run stash pick --copy
```

## View entry details

List output shows entry UUIDs. Show full details with:

```bash
poetry run stash entry show <entry-uuid>
```

Copy content to the clipboard or run a saved command:

```bash
poetry run stash entry copy <entry-uuid>              # full content
poetry run stash entry copy <entry-uuid> --first-line # command line only
poetry run stash entry run <entry-uuid>               # execute with confirmation
```

Open a saved URL in your browser:

```bash
poetry run stash open <entry-uuid>
```

## Backup and restore

```bash
poetry run stash export json ./backup.json
poetry run stash import --from-file ./backup.json
```

See [Data model](data-model.md) for export and import file formats.

## JSON output mode

Add `--json` before the subcommand for scripting:

```bash
poetry run stash --json entry list
poetry run stash --json search "git" | jq '.[].title'
```

## Try the examples

The `examples/` folder includes isolated demo scripts that use `examples/.demo-vault/` so your real vault is never touched:

```bash
./examples/scripts/01-getting-started.sh
./examples/scripts/04-import-export.sh
```

See [`examples/README.md`](../examples/README.md) for the full list.

## Next steps

- [CLI reference](cli-reference.md) — complete command list
- [Configuration](configuration.md) — environment variables and paths
- [Data model](data-model.md) — vault structure and validation rules
