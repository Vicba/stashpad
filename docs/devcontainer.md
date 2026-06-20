# Dev Container

Use a [Dev Container](https://containers.dev/) for contributor setup in VS Code or Cursor — Poetry, test dependencies, TUI/MCP extras, pre-commit hooks, and an isolated dev vault, without installing tooling on your host.

This is for **contributors**, not end users who only `pip install stashpad`.

## Open the container

1. Open the repo in VS Code or Cursor.
2. Command Palette (`Cmd+Shift+P`) → **Dev Containers: Reopen in Container**.

First build may take a few minutes. On first open, `.devcontainer/post-create.sh` runs:

- `poetry install` with test, TUI, and MCP extras
- pre-commit hooks
- isolated dev vault at `$STASH_DATA_DIR` (`.devcontainer/.stash-dev`)

Verify inside the container:

```bash
poetry run poe test
poetry run poe lint
poetry run stash --version
echo "$STASH_DATA_DIR"
```

The dev vault does not touch your host vault at `~/.config/stash`.

## After changing devcontainer files

| What changed | Action |
|--------------|--------|
| `Dockerfile` (image, apt packages) | **Dev Containers: Rebuild Container** |
| `devcontainer.json` (env, mounts) | **Rebuild Container** |
| `post-create.sh` only | **Rebuild Container**, or run `bash .devcontainer/post-create.sh` in the terminal |

Use **Rebuild Without Cache** if a normal rebuild still shows old behavior.

## Close / exit the container

**Dev Containers: Reopen Folder Locally** (or **File → Close Remote Connection**) returns you to the project on your host. Your files stay on disk; only the container session ends.

Optional: **Dev Containers: Stop Container** stops the running container before reopening locally.

You do not need to delete anything to exit. The dev vault at `.devcontainer/.stash-dev/` is gitignored.

## Optional: test from the CLI

If you have the [Dev Containers CLI](https://github.com/devcontainers/cli):

```bash
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . poetry run poe test
```

## Limitations

- Clipboard features (`stash add --clipboard`, `stash entry copy`) may not work without display forwarding; tests mock the clipboard.

## See also

- [Development](development.md) — tests, lint, project layout
- [CONTRIBUTING.md](../CONTRIBUTING.md) — PR checklist
