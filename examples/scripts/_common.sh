#!/usr/bin/env bash
# =============================================================================
# _common.sh — shared setup for all Stash example scripts
#
# Sourced by every script in this folder. Provides:
#   - A isolated demo vault (examples/.demo-vault/) so your real vault is safe
#   - A `stash` wrapper that runs via Poetry from the project root
#   - Helper functions for printing steps and resetting state
# =============================================================================

set -euo pipefail  # exit on error, unset vars, pipe failures

# Resolve paths relative to this file (works no matter where you run from)
EXAMPLES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$EXAMPLES_DIR/.." && pwd)"
VAULT_DIR="$EXAMPLES_DIR/.demo-vault"

# Tell Stash (and our wrapper) to use the demo vault, not ~/.config/stash
export STASH_DATA_DIR="$VAULT_DIR"

# Wrapper: runs `poetry run stash` with --config-dir pointing at the demo vault.
# Usage: stash entry add "Title" "content"
stash() {
  (cd "$PROJECT_ROOT" && poetry run stash --config-dir "$VAULT_DIR" "$@")
}

# Print a visible step header between command groups
banner() {
  echo ""
  echo "==> $*"
  echo ""
}

# Wipe and recreate the demo vault so each script starts from a clean slate
reset_demo_vault() {
  rm -rf "$VAULT_DIR"
  mkdir -p "$VAULT_DIR"
}
