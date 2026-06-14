#!/usr/bin/env bash
# =============================================================================
# 05-json-scripting.sh — automate Stash in shell scripts
#
# The global --json flag switches all output to JSON on stdout,
# which makes Stash composable with jq, Python, or CI pipelines.
#
# Demonstrates:
#   - JSON list / search / config output
#   - Parsing entry titles and counts from JSON
#
# Run:  ./examples/scripts/05-json-scripting.sh
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/_common.sh"

reset_demo_vault
stash init --name json-demo --force

stash entry add "JSON list" "stash --json entry list" --tag cli

# --json must come before the subcommand: stash --json entry list
# Output is a JSON array of entry objects (id, title, content, tags, ...)
banner "JSON output: list entries"
stash --json entry list

# Pipe JSON into jq or Python to extract fields for other tools
banner "Extract titles with jq (if installed)"
if command -v jq >/dev/null 2>&1; then
  stash --json entry list | jq -r '.[].title'
else
  echo "(install jq for pretty parsing — using python instead)"
  stash --json entry list | python3 -c "
import json, sys
for e in json.load(sys.stdin):
    print(e['title'])
"
fi

banner "JSON output: search"
stash --json search "json"

# Useful for debugging env/config issues
banner "JSON output: config"
stash --json config show

# Example: use JSON output in a shell variable for scripting
banner "Count entries in vault"
COUNT="$(stash --json entry list | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")"
echo "Total entries: $COUNT"
