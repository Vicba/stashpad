#!/usr/bin/env bash
# =============================================================================
# 01-getting-started.sh — your first Stash session
#
# Demonstrates the minimum workflow:
#   1. Create a vault (init)
#   2. Add entries with tags
#   3. List and search entries
#   4. Check where data is stored
#
# Run:  ./examples/scripts/01-getting-started.sh
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/_common.sh"

# Start fresh — removes any previous demo data
banner "Reset demo vault"
reset_demo_vault

# Create vault.json in examples/.demo-vault/
# --force overwrites if the vault already exists from a prior run
banner "Initialize vault"
stash init --name demo --force

# `entry add` takes two positional args: TITLE and CONTENT
# --tag can be repeated; tags help filter later with `entry list --tag`
banner "Add two entries"
stash entry add "Hello Stash" "Your first saved note" --tag demo
stash entry add "List entries" "stash entry list" --tag demo --tag cli

# Default output is a Rich table in the terminal
banner "List all entries (table)"
stash entry list

# Search scans title, content, URL, and tags (case-insensitive)
banner "Search for 'list'"
stash search "list"

# Prints the directory where vault.json lives
banner "Show config path"
stash config path

banner "Done — demo vault at: $VAULT_DIR"
