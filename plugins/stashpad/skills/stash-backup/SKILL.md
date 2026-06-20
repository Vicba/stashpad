---
name: stash-backup
description: |
  Backup, restore, and migrate a Stashpad vault between machines.
  Use when the user wants to export, import, back up, restore, dry-run validate,
  or move their stash vault to a new computer.
---

# Stashpad Backup

Export and import vault data. See `examples/recipes/backup-and-restore.md` for full recipes.

## Before you start

Confirm the active vault:

```bash
stash config path
stash entry list --limit 5
```

Warn the user before any operation that overwrites data (`stash init --force`, import into production vault).

## Export backup

```bash
mkdir -p ~/stash-backups
stash export json ~/stash-backups/stash-$(date +%Y%m%d).json
stash export markdown ~/stash-backups/stash-$(date +%Y%m%d).md
```

| Format | Use case |
|--------|----------|
| JSON | Machine-readable; use for re-import |
| Markdown | Human-readable archive |

## Validate before importing

Always dry-run first:

```bash
stash import --from-file ~/stash-backups/stash-20250614.json --dry-run
```

Pydantic validates every entry — invalid URLs or empty titles fail early.

## Restore on a new machine

```bash
pip install stashpad
stash init --name restored --force
stash import --from-file ~/stash-backups/stash-20250614.json
stash entry list
```

Import accepts:
- A JSON array of entries
- A full vault export (object with `"entries"` key)

## Sandbox import (safe testing)

Test an import without touching the personal vault:

```bash
STASH_DATA_DIR=/tmp/stash-sandbox stash init --name sandbox --force
STASH_DATA_DIR=/tmp/stash-sandbox stash import --from-file backup.json --dry-run
STASH_DATA_DIR=/tmp/stash-sandbox stash import --from-file backup.json
STASH_DATA_DIR=/tmp/stash-sandbox stash entry list
```

## Merge vs replace

- Import **adds** entries to the existing vault (does not wipe it)
- To start fresh, use `stash init --force` first (with user consent), then import

## Recommended backup schedule

Suggest periodic JSON exports:

```bash
stash export json ~/stash-backups/stash-$(date +%Y%m%d).json
```

Keep at least one Markdown export for readability.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Validation errors on dry-run | Inspect failing entries in the JSON; fix URLs/titles |
| Empty import | Check file format (array vs `{ "entries": [...] }`) |
| Wrong vault | Set `STASH_DATA_DIR` before init/import |
