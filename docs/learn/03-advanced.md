# Advanced

## Typer Callback & Context

- **Docs:** [Typer Callback](https://typer.tiangolo.com/tutorial/commands/callback/), [Using the Context](https://typer.tiangolo.com/tutorial/commands/context/)
- **Code:** `src/stash_cli/cli.py`, `context.py`

Global `--verbose`, `--json`, `--config-dir` stored in `ctx.obj` as `AppContext`.

## Version (is_eager)

- **Docs:** [Version Option](https://typer.tiangolo.com/tutorial/options/version/)
- **Code:** `context.py` → `version_callback`

## Path & File types

- **Docs:** [Path](https://typer.tiangolo.com/tutorial/parameter-types/path/), [File](https://typer.tiangolo.com/tutorial/parameter-types/file/)
- **Code:** `commands/export.py`, `commands/import_cmd.py`

```bash
poetry run stash export json ./backup.json
poetry run stash import --from-file ./entries.json
```

## Custom types

- **Docs:** [Custom Types](https://typer.tiangolo.com/tutorial/parameter-types/custom-types/)
- **Code:** `src/stash_cli/types.py` → `validate_url()`

## Autocompletion

- **Docs:** [CLI Option autocompletion](https://typer.tiangolo.com/tutorial/options-autocompletion/)
- **Code:** `src/stash_cli/completions.py`

Tag names complete on `--tag` options.

## Progress bar

- **Docs:** [Progress Bar](https://typer.tiangolo.com/tutorial/progressbar/)
- **Code:** `import_cmd.py`, `export.py`

Bulk import/export shows Rich progress bars.

## Launching applications

- **Docs:** [Launching Applications](https://typer.tiangolo.com/tutorial/launch/)
- **Code:** `commands/open_cmd.py`

```bash
poetry run stash open <entry-id>
```

## CLI Application Directory

- **Docs:** [CLI Application Directory](https://typer.tiangolo.com/tutorial/app-dir/)
- **Code:** `storage.py`, `config.py`

Vault stored at `~/.config/stash/vault.json` (XDG). Override with `STASH_DATA_DIR`.

## Exceptions and errors

- **Docs:** [Exceptions and Errors](https://typer.tiangolo.com/tutorial/exceptions/)
- **Code:** `exceptions.py`, `typer.BadParameter`, `typer.Exit`

## One file per command

- **Docs:** [One File Per Command](https://typer.tiangolo.com/tutorial/one-file-per-command/)
- **Code:** `src/stash_cli/commands/` — each command group in its own module

## typer command

- **Docs:** [typer command](https://typer.tiangolo.com/tutorial/typer-command/)

```bash
poetry run poe dev -- entry list
```
