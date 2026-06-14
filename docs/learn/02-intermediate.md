# Intermediate

## Ask with Prompt & Password

- **Docs:** [Ask with Prompt](https://typer.tiangolo.com/tutorial/prompt/), [Password Option](https://typer.tiangolo.com/tutorial/options/password/)
- **Code:** `src/stash_cli/commands/init.py`

```bash
poetry run stash init --name my-vault
poetry run stash entry add --interactive
```

`init` prompts for vault name; `--api-token` uses hidden input with confirmation callback.

## Required CLI Options

- **Docs:** [Required CLI Options](https://typer.tiangolo.com/tutorial/options/required/)
- **Code:** `entry edit --title` (required), `config set --key` (required)

## CLI Arguments with Environment Variables

- **Docs:** [Arguments envvar](https://typer.tiangolo.com/tutorial/arguments/envvar/)
- **Code:** `init [DATA_DIR]` reads `STASH_DATA_DIR`

```bash
STASH_DATA_DIR=/tmp/my-stash poetry run stash init --force
```

## Enum & DateTime & Boolean

- **Docs:** [Enum](https://typer.tiangolo.com/tutorial/parameter-types/enum/), [DateTime](https://typer.tiangolo.com/tutorial/parameter-types/datetime/), [Boolean](https://typer.tiangolo.com/tutorial/parameter-types/bool/)
- **Code:** `models.py` (`Priority`, `SortOrder`), `entry list --since`

```bash
poetry run stash entry list --since 2025-01-01 --sort title
```

## Option callback

- **Docs:** [Option Callback](https://typer.tiangolo.com/tutorial/options/callback/)
- **Code:** `_validate_since()` in `entry.py` validates date format

## SubCommands

- **Docs:** [SubCommands](https://typer.tiangolo.com/tutorial/subcommands/)
- **Code:** `cli.py` mounts `entry`, `tags`, `export`, `config` sub-apps

All entry commands live in one file (`commands/entry.py`) — see [SubCommands in a Single File](https://typer.tiangolo.com/tutorial/subcommands/single-file/).

## Nested subcommands & callback override

- **Docs:** [Nested SubCommands](https://typer.tiangolo.com/tutorial/subcommands/add-typer/), [Callback Override](https://typer.tiangolo.com/tutorial/subcommands/callback-override/)
- **Code:** `commands/tags.py`

```bash
poetry run stash tags --prefix dev list
```

## Multiple values

- **Docs:** [Multiple CLI Options](https://typer.tiangolo.com/tutorial/multiple-values/multiple-options/), [Options with Multiple Values](https://typer.tiangolo.com/tutorial/multiple-values/options-with-multiple-values/), [Arguments with Multiple Values](https://typer.tiangolo.com/tutorial/multiple-values/arguments-with-multiple-values/)
- **Code:** `entry.py`

```bash
# Repeated --tag
poetry run stash entry add "T" "C" --tag python --tag cli

# Comma-separated --tags filter
poetry run stash entry list --tags python,cli

# Multiple positional IDs
poetry run stash entry rm <id1> <id2> --force
```

## Confirmations

`entry remove` and `tags remove` use `typer.confirm()` unless `--force`.
