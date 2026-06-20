# Contributing to Stashpad

Thanks for your interest in contributing to **Stashpad** (`stash` CLI). This guide covers how to get set up, submit changes, and what we expect in pull requests.

For deeper technical detail (project layout, architecture, isolated vaults), see [docs/development.md](docs/development.md).

## Ways to contribute

- Report bugs or suggest features via [GitHub Issues](https://github.com/Vicba/stash-cli/issues)
- Fix bugs or implement features via pull request
- Improve documentation, examples, or tests
- Share feedback on CLI ergonomics and workflows

Use the issue templates when opening a bug report, feature request, or improvement.

## Development setup

**Requirements:** Python 3.8–3.12, [Poetry](https://python-poetry.org/)

```bash
git clone https://github.com/Vicba/stash-cli.git
cd stash-cli
poetry install
```

### Dev Container (alternative)

If you use VS Code or Cursor, open the repo and choose **Reopen in Container**. Dependencies (including TUI and MCP extras), pre-commit hooks, and an isolated dev vault are set up via `.devcontainer/post-create.sh`.

```bash
poetry run poe test
poetry run poe lint
poetry run stash --help
```

Dev vault path: `$STASH_DATA_DIR` (defaults to `.devcontainer/.stash-dev` inside the container). Clipboard features may not work without display forwarding; tests mock the clipboard.

Run the CLI locally:

```bash
poetry run stash --help
poetry run poe dev -- --help   # Typer dev runner
```

Use an isolated vault while experimenting so you do not touch your personal data:

```bash
export STASH_DATA_DIR=/tmp/stash-dev
poetry run stash init --name dev --force
```

## Before you open a pull request

1. **Branch from `main`** — use a descriptive branch name, e.g. `fix/search-ranking` or `feat/pick-filters`.
2. **Write or update tests** — CLI behavior is tested with `pytest` and `typer.testing.CliRunner`. Add coverage for new commands, flags, and edge cases.
3. **Run the test suite:**

   ```bash
   poetry run poe test
   ```

4. **Run lint and type checks:**

   ```bash
   poetry run poe lint
   ```

   This runs `safety check` and all pre-commit hooks (ruff, mypy, shellcheck, and more).

5. **Install pre-commit hooks** (recommended):

   ```bash
   poetry run pre-commit install --install-hooks
   ```

   Hooks run automatically on commit and enforce formatting, static analysis, and commit message format.

6. **Update docs** when behavior is user-visible:
   - `docs/cli-reference.md` for new or changed commands/flags
   - `README.md` command summary when appropriate
   - `CHANGELOG.md` is updated at release time by maintainers; you do not need to bump the version

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) via [Commitizen](https://commitizen-tools.github.io/commitizen/). Pre-commit validates messages on `commit-msg`.

Use a type, optional scope, and short description:

```
feat(pick): add --tag filter to interactive picker
fix(storage): persist pin toggles on edit
docs: document STASH_DATA_DIR in configuration guide
test: cover fuzzy search with exact flag
refactor: extract clipboard helper from entry add
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `perf`.

## Code style

- **Formatting and linting:** [Ruff](https://docs.astral.sh/ruff/) (`line-length = 100`, NumPy docstring convention)
- **Types:** strict [mypy](https://mypy.readthedocs.io/) on `src/`
- **Imports:** no relative imports in application code
- **CLI commands:** one module per command group under `src/stashpad/commands/`
- **Validation:** Pydantic schemas in `schemas.py` / `models.py` for user input

Match existing patterns in the file you are editing. Prefer small, focused changes over large refactors unless discussed first.

## Pull request checklist

- [ ] Tests pass locally (`poetry run poe test`)
- [ ] Lint passes (`poetry run poe lint`)
- [ ] Commit messages follow Conventional Commits
- [ ] User-facing changes are documented in `docs/` (and README if relevant)
- [ ] PR description explains what changed and why

CI runs on every pull request to `main`:

- `pytest` on Python 3.11 and 3.12
- `ruff check` on `src` and `tests`
- CLI smoke test (`stash --version`, `--help`, getting-started example script)

## Project structure (quick reference)

```
src/stashpad/
  cli.py              # root Typer app
  context.py          # shared AppContext
  storage.py          # JSON vault persistence
  commands/           # one module per command group
tests/                # pytest CLI tests
docs/                 # user and developer reference
examples/             # runnable scripts and sample vault
```

## Questions

Open a [GitHub Discussion or Issue](https://github.com/Vicba/stash-cli/issues) if you are unsure whether a change fits, or want feedback before investing in a large PR.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE) that covers this project.
