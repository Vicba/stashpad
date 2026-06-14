# Backup and restore

Keep your snippet library safe and move it between machines.

## Export a backup

```bash
mkdir -p ~/stash-backups
stash export json ~/stash-backups/stash-$(date +%Y%m%d).json
stash export markdown ~/stash-backups/stash-$(date +%Y%m%d).md
```

Markdown is human-readable; JSON is for re-import.

## Restore on a new machine

```bash
poetry install
stash init --name restored --force

# From a JSON array of entries
stash import --from-file ~/stash-backups/stash-20250614.json

# From a full vault export (has "entries" key)
stash import --from-file examples/data/team-backup.json

stash entry list
```

## Validate before importing

```bash
stash import --from-file backup.json --dry-run
```

Pydantic validates every entry — invalid URLs or empty titles fail early.

## Use a separate vault for experiments

```bash
STASH_DATA_DIR=/tmp/stash-sandbox stash init --name sandbox --force
STASH_DATA_DIR=/tmp/stash-sandbox stash entry add "Test" "content"
```

Or use the example scripts — they always target `examples/.demo-vault/`.
