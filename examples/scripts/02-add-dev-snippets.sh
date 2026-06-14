#!/usr/bin/env bash
# =============================================================================
# 02-add-dev-snippets.sh — build a tagged snippet library
#
# Shows how developers typically use Stash day-to-day:
#   - Save shell commands you look up repeatedly
#   - Attach URLs to official docs
#   - Set priority (high / medium / low)
#   - Filter entries by tag or priority
#
# Run:  ./examples/scripts/02-add-dev-snippets.sh
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/_common.sh"

reset_demo_vault
stash init --name dev-snippets --force

# --url links to docs; use `stash open <id>` later to open in browser
# --priority high marks entries you reach for every week
banner "Add Docker snippets"
stash entry add \
  "Docker prune" \
  "docker system prune -af" \
  --tag docker --tag devops \
  --url "https://docs.docker.com/config/pruning/" \
  --priority high

stash entry add \
  "Docker compose logs" \
  "docker compose logs -f --tail=100" \
  --tag docker --tag devops

banner "Add Git snippets"
stash entry add \
  "Git undo last commit" \
  "git reset --soft HEAD~1" \
  --tag git \
  --priority high

stash entry add \
  "Git stash pop" \
  "git stash pop" \
  --tag git

banner "Add Python snippets"
stash entry add \
  "Run tests with Poetry" \
  "poetry run pytest -v" \
  --tag python --tag testing

# --priority filters to one enum value: low | medium | high
banner "List high-priority entries"
stash entry list --priority high

# --tag filters entries that contain this tag (repeatable for AND logic)
banner "List docker-tagged entries"
stash entry list --tag docker

# Tags subcommand lists the tag registry (not just tags on one entry)
banner "List all tags"
stash tags list

banner "Done"
