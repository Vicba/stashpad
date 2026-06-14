# Professional CLI Patterns

Patterns used in Stash beyond the Typer docs.

## Structured exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Vault not initialized |
| 3 | Entry not found |
| 4 | Storage error |
| 5 | Validation error |

Defined in `src/stash_cli/exceptions.py`.

## JSON output mode

`--json` on any command emits machine-readable output. Useful for scripting:

```bash
poetry run stash --json entry list | jq '.[0].id'
```

Implemented via `AppContext.json_output` in `output.py`.

## XDG config directory

Vault data lives in `~/.config/stash/` following the [XDG Base Directory spec](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html). Override with `STASH_DATA_DIR`.

## Atomic writes

`storage.py` writes to a temp file then `os.replace()` — prevents corrupted vault on crash.

## Separation of concerns

```
commands/  → Typer CLI (user interface)
storage.py → persistence (business logic)
models.py  → data shapes
api.py     → HTTP adapter (same storage)
```

## Error UX

- Errors go to stderr via `typer.echo(..., err=True)`
- Human-readable messages, not stack traces (unless `--verbose`)
