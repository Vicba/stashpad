# Stash CLI Examples

Practical examples for using **Stash** — save commands, snippets, URLs, and notes from the terminal.

All scripts use an **isolated demo vault** at `examples/.demo-vault/` so your real vault at `~/.config/stash/` is never touched.

## Prerequisites

From the project root:

```bash
poetry install
```

## Quick try (30 seconds)

```bash
./examples/scripts/01-getting-started.sh
```

## What's in this folder

```
examples/
├── README.md                 # this file
├── data/                     # sample JSON for import
│   ├── sample-entries.json   # a few entries to import
│   └── team-backup.json      # larger export-shaped file
├── scripts/                  # runnable bash walkthroughs
│   01-getting-started.sh
│   02-add-dev-snippets.sh
│   03-search-and-filter.sh
│   04-import-export.sh
│   05-json-scripting.sh
└── recipes/                  # prose guides for common workflows
    daily-workflow.md
    backup-and-restore.md
    api-workflow.md
```

## Run any script

```bash
chmod +x examples/scripts/*.sh   # once
./examples/scripts/02-add-dev-snippets.sh
```

## Use your real vault

Drop the `--config-dir` flag (or unset `STASH_DATA_DIR`) and run commands directly:

```bash
poetry run stash init --name my-vault
poetry run stash entry add "Git undo" "git reset --soft HEAD~1" --tag git
```

## Sample data only (no scripts)

Import the bundled JSON into any vault:

```bash
poetry run stash init --name imported --force
poetry run stash import --from-file examples/data/sample-entries.json
poetry run stash entry list
```
