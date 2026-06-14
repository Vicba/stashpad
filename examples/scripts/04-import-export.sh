#!/usr/bin/env bash
# =============================================================================
# 04-import-export.sh — backup, restore, and share entries as files
#
# Demonstrates moving data in and out of Stash:
#   - Import from JSON (array of entries OR full vault object)
#   - Dry-run to validate without writing
#   - Export to JSON (for re-import) or Markdown (for reading/sharing)
#
# Sample files live in examples/data/
#
# Run:  ./examples/scripts/04-import-export.sh
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/_common.sh"

# Exported files land here (gitignored via examples/.gitignore)
EXPORT_DIR="$EXAMPLES_DIR/exports"
mkdir -p "$EXPORT_DIR"

reset_demo_vault
stash init --name import-export-demo --force

# --dry-run parses and validates JSON with Pydantic but does not save
banner "Dry-run import (validate only)"
stash import --from-file "$EXAMPLES_DIR/data/sample-entries.json" --dry-run

# sample-entries.json is a plain JSON array: [{title, content, tags, ...}, ...]
banner "Import sample entries"
stash import --from-file "$EXAMPLES_DIR/data/sample-entries.json"

# team-backup.json is vault-shaped: {metadata, entries, tags}
banner "Import team backup (vault-shaped JSON)"
stash import --from-file "$EXAMPLES_DIR/data/team-backup.json"

banner "List everything"
stash entry list --limit 20

# export json writes a JSON array you can re-import on another machine
banner "Export to JSON"
stash export json "$EXPORT_DIR/my-backup.json"

# export markdown produces a human-readable document with headings and code blocks
banner "Export to Markdown"
stash export markdown "$EXPORT_DIR/my-backup.md"

banner "Exported files"
ls -la "$EXPORT_DIR"

banner "Preview markdown export (first 15 lines)"
head -15 "$EXPORT_DIR/my-backup.md"
