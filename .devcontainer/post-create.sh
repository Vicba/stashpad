#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Docker volume mounts for the Poetry cache are created as root.
sudo mkdir -p /home/vscode/.cache/pypoetry
sudo chown -R vscode:vscode /home/vscode/.cache

# Recreate venv if it was built for a different workspace mount path.
if [[ -f .venv/pyvenv.cfg ]] && ! grep -q "${PWD}/.venv" .venv/pyvenv.cfg; then
  rm -rf .venv
fi

poetry install --no-interaction --with test -E tui -E mcp
poetry run pre-commit install --install-hooks

mkdir -p "${STASH_DATA_DIR}"
poetry run stash init --name dev --force || true

poetry run stash --version
