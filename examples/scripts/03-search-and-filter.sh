#!/usr/bin/env bash
# =============================================================================
# 03-search-and-filter.sh — find, edit, and delete entries
#
# Covers intermediate CLI features:
#   - Full-text search
#   - Tag filters (--tag vs --tags)
#   - Sort order
#   - JSON output to grab an entry ID for other commands
#   - Edit and remove (with alias `entry rm`)
#
# Run:  ./examples/scripts/03-search-and-filter.sh
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/_common.sh"

reset_demo_vault
stash init --name filters-demo --force

# Seed three entries with different tags for filtering demos
# --tag is repeatable; --tags accepts comma-separated values (same effect here)
stash entry add "Alpha" "first entry" --tag alpha --tags demo
stash entry add "Beta" "second entry with docker keyword" --tag beta --tag docker
stash entry add "Gamma" "third entry" --tag gamma --tags demo

# Search is broader than list — matches partial text in title/content/url/tags
banner "Search by keyword"
stash search "docker"

# --tags work,python,docker  →  entry must have ALL listed tags
banner "Filter: comma-separated tags (--tags demo)"
stash entry list --tags demo

# --tag alpha --tag demo  →  entry must have BOTH tags (AND, not OR)
banner "Filter: repeated --tag flags"
stash entry list --tag alpha --tag demo

# SortOrder enum: newest | oldest | title
banner "Sort by title"
stash entry list --sort title

# --json makes stdout machine-readable; we parse the first entry's UUID
# That UUID is needed for show / edit / rm / open commands
banner "Get entry ID as JSON, then show full detail"
ENTRY_ID="$(stash --json entry list --limit 1 | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")"
echo "Entry ID: $ENTRY_ID"
stash entry show "$ENTRY_ID"

# edit requires --title (required option demo); other fields are optional
banner "Edit entry title"
stash entry edit "$ENTRY_ID" --title "Alpha (edited)"

# rm is a hidden alias for remove; --force skips the confirmation prompt
banner "Remove entry (with --force to skip prompt)"
stash entry rm "$ENTRY_ID" --force

# ls is a hidden alias for list
banner "Remaining entries"
stash entry ls
