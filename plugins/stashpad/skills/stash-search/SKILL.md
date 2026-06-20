---
name: stash-search
description: |
  Find, list, copy, and run entries in a Stashpad vault.
  Use when the user wants to search, find, pick, or retrieve a saved command,
  snippet, URL, or note. Supports fuzzy search, tags, pins, copy-to-clipboard, and run.
---

# Stashpad Search

Retrieve saved entries. See `examples/recipes/daily-workflow.md` for daily patterns.

## MCP path (preferred when connected)

| Tool | When to use |
|------|-------------|
| `stash_search` | Fuzzy search by title, content, URL, tags |
| `stash_list` | Filter by tags, kind, pinned, sort order |
| `stash_get` | Fetch one entry by UUID |

### stash_search parameters

- `query` (required) — search text
- `limit` — max results (default 20)
- `exact` — disable fuzzy matching

### stash_list parameters

- `tags` — entries must have **all** listed tags
- `kind` — `command`, `url`, `snippet`, `note`
- `pinned` — filter pinned entries
- `limit`, `sort` — `newest`, `oldest`, `title`

Present results clearly: title, tags, and content preview. Include entry UUID when the user may need to copy or run.

## CLI path

### Quick search

```bash
stash search "docker prune"        # fuzzy
stash search "prn"                 # fuzzy abbreviation
stash search "exact term" --exact
```

### Pinned and interactive pick

```bash
stash pins
stash pick deploy                  # fzf-style picker
stash pick kubectl --copy          # copy selected entry
```

### Filtered listing

```bash
stash entry list --tag devops
stash entry list --tags node,setup
stash entry list --priority high
stash entry list --since 2025-01-01 --sort newest --limit 10
```

### JSON output for scripting

```bash
stash --json search "deploy"
stash --json entry list --tag prod | jq '.entries[].id'
```

## Copy or run an entry

Get the entry UUID from search/list output, then:

```bash
# Copy command to clipboard (first line only)
stash entry copy <entry-uuid> --first-line

# Run with confirmation prompt
stash entry run <entry-uuid>
```

**Always confirm with the user before `stash entry run`** — it executes shell commands.

## Open a saved URL

```bash
stash open <entry-uuid>
```

## Search strategy

1. Start with `stash pins` if the user mentions favorites
2. Try fuzzy `stash search` with keywords from the user's description
3. Narrow with `--tag` if domain is known (e.g. `k8s`, `docker`, `git`)
4. Use `stash pick` when the user wants interactive selection

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No results | Try shorter/fuzzy terms; check `stash entry list` |
| Wrong vault | Verify `stash config path` and `STASH_DATA_DIR` |
| pick requires fzf | Install `fzf` or use `stash search` instead |
