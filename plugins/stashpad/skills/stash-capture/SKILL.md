---
name: stash-capture
description: |
  Save commands, URLs, snippets, and notes to a Stashpad vault.
  Use when the user wants to stash, save, or capture a shell command, curl one-liner,
  URL, code snippet, or note with tags and priority. Handles clipboard and stdin capture.
---

# Stashpad Capture

Save entries to the user's vault. See `examples/recipes/daily-workflow.md` for patterns.

## Prerequisites

Vault must exist. If unsure, run `stash config path` and `stash init` if needed (see **stash-setup**).

## MCP path (preferred when connected)

If `stash_add` MCP tool is available and write mode is enabled:

| Parameter | Usage |
|-----------|-------|
| `title` | Short descriptive name |
| `content` | Command body, snippet, or note text |
| `url` | Optional http(s) URL |
| `tags` | List of tag strings |
| `kind` | `command`, `url`, `snippet`, or `note` (auto-inferred if omitted) |
| `pinned` | `true` for frequently used entries |

Example: save a curl command with tag `api`.

If MCP is read-only, tell the user write mode requires removing `--read-only` from MCP config, or use CLI below.

## CLI path

### Quick add (alias)

```bash
stash add "Title" "command or content" --tag devops --priority high
```

### Full entry add

```bash
stash entry add "Docker prune" "docker system prune -af" \
  --tag devops --tag docker \
  --url https://docs.docker.com/config/pruning/ \
  --priority high
```

### Capture from chat context

When the user shares a command in conversation, construct the add command with:
- **Title**: concise label (what it does, not the full command)
- **Content**: exact command text — preserve quoting and flags
- **Tags**: infer from context (e.g. `docker`, `git`, `node`, `api`)

```bash
stash add "Kubectl port-forward" "kubectl port-forward svc/my-svc 8080:80" --tag k8s
```

### Clipboard capture

```bash
stash add "Clipboard snippet" --clipboard --tag misc
```

### Stdin / piped content

```bash
git log --oneline -5 | stash add "Recent commits" -
echo "snippet text" | stash entry add "My snippet" -
```

### Interactive mode

When title/content are unclear:

```bash
stash entry add --interactive
```

## Tagging and priority

```bash
# Repeat --tag or use comma-separated
stash add "Deploy script" "./deploy.sh" --tag deploy --tag prod
stash entry add "Weekly task" "npm audit fix" --priority high
```

## Duplicate detection

Stashpad warns on duplicate content. If the user wants to update an existing entry, use `stash entry edit <id>` instead of adding again. Find the ID with `stash search` first.

## After capture

Confirm success:

```bash
stash search "<title keyword>"
# or with --json for scripting:
stash --json search "<keyword>"
```

## Tips

- Use `--priority high` for weekly-use commands
- Add `--url` when the entry references documentation
- Kind is inferred: URLs → `url`, shell-like text → `command`, else `snippet` or `note`
