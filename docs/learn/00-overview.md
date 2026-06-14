# Overview

Stash is a **real CLI** that teaches **every section** of the [Typer tutorial](https://typer.tiangolo.com/tutorial/). You learn by reading code, running commands, and following the curriculum.

## What Stash does

Developers constantly look up the same things: Docker commands, git aliases, API URLs, regex patterns. Stash stores these as **entries** with tags, priority, and optional URLs — searchable from the terminal or via REST API.

## Learning path

| Level | Doc | What you build |
|-------|-----|----------------|
| Setup | [00-setup.md](00-setup.md) | Install, env vars, packaging |
| Beginner | [01-beginner.md](01-beginner.md) | `entry add`, `list`, `show`, help, version |
| Intermediate | [02-intermediate.md](02-intermediate.md) | `init`, tags, filters, confirmations |
| Advanced | [03-advanced.md](03-advanced.md) | export/import, autocompletion, open |
| Testing | [04-testing.md](04-testing.md) | CliRunner test patterns |
| Pro patterns | [05-professional-patterns.md](05-professional-patterns.md) | exit codes, JSON mode, XDG dirs |
| Click | [06-click-internals.md](06-click-internals.md) | Typer ↔ Click relationship |

## Try it now

```bash
poetry run stash init --name demo --force
poetry run stash entry add "Git undo commit" "git reset --soft HEAD~1" --tag git
poetry run stash entry list
```

## Find code for any Typer topic

See [COMMAND_MAP.md](COMMAND_MAP.md) — maps every Typer sidebar item to a source file and example command.
