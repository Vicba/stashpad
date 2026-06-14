# Typer Tutorial → Stash Code Map

Complete mapping of every [Typer Learn](https://typer.tiangolo.com/tutorial/) section to runnable code or docs in this repo.

| Typer doc section | Type | Location | Example |
|---|---|---|---|
| Environment Variables | code | `cli.py`, `config.py` | `STASH_DATA_DIR=... stash init` |
| Virtual Environments | docs | [00-setup.md](00-setup.md) | `poetry install` |
| Install Typer | docs | [00-setup.md](00-setup.md) | in `pyproject.toml` deps |
| First Steps | code | `cli.py` | `stash --help` |
| Typer App | code | `cli.py` | root `app = typer.Typer(...)` |
| Printing and Colors | code | `output.py` | `stash entry show <id>` |
| Terminating | code | `exceptions.py` | vault not init → exit 2 |
| CLI Arguments | code | `commands/entry.py` | `stash entry add TITLE CONTENT` |
| Optional CLI Arguments | code | `commands/search.py` | `stash search` (optional query) |
| CLI Arguments with Default | code | `commands/entry.py` | list defaults |
| CLI Arguments with Help | code | all commands | `--help` on any command |
| CLI Arguments with envvar | code | `commands/init.py` | `STASH_DATA_DIR` on `[DATA_DIR]` |
| CLI Options | code | `commands/entry.py` | `--tag`, `--limit` |
| CLI Options with Help | code | all commands | `--help` |
| Required CLI Options | code | `entry edit`, `config set` | `--title`, `--key` required |
| CLI Option Prompt | code | `commands/init.py` | `--name` prompts |
| Password + Confirmation | code | `commands/init.py` | `--api-token` |
| CLI Option Name | code | all commands | `-f`/`--from-file`, `-v`/`--verbose` |
| CLI Option Callback | code | `entry.py` | `_validate_since()` |
| Version Option (is_eager) | code | `context.py` | `stash --version` |
| Command CLI Arguments | code | `commands/entry.py` | positional args |
| Command CLI Options | code | `commands/entry.py` | `--priority` |
| Command Help | code | all commands | docstrings → help text |
| Custom Command Name | code | `entry.py` | `entry ls`, `entry rm` |
| Typer Callback | code | `cli.py` | `@app.callback()` |
| One or Multiple Commands | code | `cli.py` | init, search, entry, tags, ... |
| Using the Context | code | `context.py` | `ctx.obj = AppContext(...)` |
| CLI Option autocompletion | code | `completions.py` | `--tag` completion |
| Number | code | `entry list --limit` | `--limit 10` |
| Boolean | code | `--force`, `--dry-run` | `entry rm --force` |
| UUID | code | `entry show/remove` | UUID args |
| DateTime | code | `entry list --since` | date filters |
| Enum | code | `models.py` | `Priority`, `SortOrder` |
| Path | code | `export.py`, `import_cmd.py` | file paths |
| File | code | `import_cmd.py` | `--from-file` |
| Custom Types | code | `types.py` | `validate_url()` |
| SubCommands — Add Typer | code | `cli.py` | `add_typer(entry_app)` |
| SubCommands — Single File | code | `commands/entry.py` | all entry cmds in one file |
| Nested SubCommands | code | `commands/tags.py` | `stash tags list` |
| Sub-Typer Callback Override | code | `commands/tags.py` | `--prefix` on tags group |
| SubCommand Name and Help | code | `cli.py` | `name="entry"` |
| Multiple CLI Options | code | `entry add --tag A --tag B` | repeated flags |
| Options with Multiple Values | code | `entry list --tags a,b,c` | comma-separated |
| Arguments with Multiple Values | code | `entry rm ID ID...` | bulk delete |
| Ask with Prompt | code | `init`, `entry add -i` | interactive mode |
| Progress Bar | code | `import_cmd.py`, `export.py` | bulk operations |
| CLI Application Directory | code | `storage.py` | `~/.config/stash/` |
| Launching Applications | code | `open_cmd.py` | `stash open <id>` |
| Testing | code | `tests/test_cli.py` | CliRunner |
| Building a Package | code+docs | `pyproject.toml`, [00-setup.md](00-setup.md) | `poetry install` |
| Exceptions and Errors | code | `exceptions.py` | custom errors |
| One File Per Command | code | `commands/` | module per group |
| typer command | code+docs | `pyproject.toml` poe dev | `poe dev` |
| Vendored Click | docs | [06-click-internals.md](06-click-internals.md) | Click relationship |
