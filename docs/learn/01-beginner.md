# Beginner

## First Steps & Typer App

- **Docs:** [First Steps](https://typer.tiangolo.com/tutorial/first-steps/), [Typer App](https://typer.tiangolo.com/tutorial/typer-app/)
- **Code:** `src/stash_cli/cli.py`

```bash
poetry run stash --help
poetry run stash --version
```

## CLI Arguments

- **Docs:** [CLI Arguments](https://typer.tiangolo.com/tutorial/arguments/)
- **Code:** `src/stash_cli/commands/entry.py` → `add`

```bash
poetry run stash entry add "Title" "Content body"
```

Positional `title` and `content` are required strings.

## CLI Options

- **Docs:** [CLI Options](https://typer.tiangolo.com/tutorial/options/)
- **Code:** `entry list --limit`, `entry add --priority`

```bash
poetry run stash entry list --limit 5 --priority high
```

## Printing and Colors

- **Docs:** [Printing and Colors](https://typer.tiangolo.com/tutorial/printing/)
- **Code:** `src/stash_cli/output.py`

Rich tables in `entry list`, panels in `entry show`.

## Terminating

- **Docs:** [Terminating](https://typer.tiangolo.com/tutorial/terminating/)
- **Code:** `src/stash_cli/exceptions.py`

Custom exit codes: vault not initialized (2), entry not found (3).

## Parameter types: Number, UUID

- **Docs:** [Number](https://typer.tiangolo.com/tutorial/parameter-types/number/), [UUID](https://typer.tiangolo.com/tutorial/parameter-types/uuid/)
- **Code:** `--limit` (int), `entry show <uuid>`

## Custom command names

- **Docs:** [Custom Command Name](https://typer.tiangolo.com/tutorial/commands/name/)
- **Code:** `entry ls` alias for `entry list`, `entry rm` for `remove`

```bash
poetry run stash entry ls
```

## Command help

Every command supports `--help`. Try:

```bash
poetry run stash entry add --help
```
