# Data model

Stash persists everything in a single JSON file: `<data_dir>/vault.json`.

## Vault structure

```json
{
  "metadata": {
    "name": "my-vault",
    "created_at": "2025-06-14T10:00:00+00:00",
    "version": "1"
  },
  "entries": [],
  "tags": []
}
```

| Field | Description |
|-------|-------------|
| `metadata.name` | Human-readable vault name set during `stash init` |
| `metadata.created_at` | UTC timestamp when the vault was created |
| `metadata.version` | Vault schema version |
| `entries` | List of reference entries |
| `tags` | Registry of known tag names (may include tags not currently on any entry) |

Writes are atomic: the storage layer writes to a temporary file and replaces `vault.json` on success.

## Entry

Each entry represents a saved command, snippet, URL, or note.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | auto | Unique identifier |
| `title` | string | yes | Short label (min length 1, whitespace trimmed) |
| `content` | string | yes | Body text |
| `url` | string | no | http or https URL |
| `tags` | string[] | no | Normalized lowercase tags |
| `priority` | enum | no | `low`, `medium`, or `high` (default: `medium`) |
| `created_at` | datetime | auto | UTC creation time |
| `updated_at` | datetime | auto | UTC last update time |
| `opened_at` | datetime | no | UTC last view/use time (`show`, `copy`, `run`, `open`) |
| `pinned` | boolean | no | Favorite flag for `stash pins` (default: `false`) |

Example entry:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Docker prune",
  "content": "docker system prune -af",
  "url": "https://docs.docker.com/config/pruning/",
  "tags": ["devops", "docker"],
  "priority": "high",
  "created_at": "2025-06-14T10:00:00+00:00",
  "updated_at": "2025-06-14T10:00:00+00:00",
  "opened_at": null,
  "pinned": false
}
```

## Validation

Input is validated with Pydantic before it is saved:

| Schema | Used for |
|--------|----------|
| `EntryCreate` | New entries (`entry add`) |
| `EntryUpdate` | Partial edits (`entry edit`) |
| `EntryFilter` | List filters (`entry list`) |
| `SearchQuery` | Search (`search`) |
| `ImportPayload` | JSON import files |

Common validation rules:

- Titles cannot be empty after trimming
- URLs must use `http://` or `https://`
- Tags are normalized to lowercase and deduplicated
- Invalid import files fail with a clear error before any data is written

## Tags

Tags serve two roles:

1. **On entries** — labels for filtering and search
2. **In the registry** — the vault-level `tags` list tracks known tag names

Add tags to entries with `--tag` / `--tags` on `entry add` or `entry edit`. Register a tag without an entry via `stash tags add`.

List tags with optional prefix filter:

```bash
stash tags list
stash tags --prefix dev list
```

## Import format

`stash import` accepts JSON in either shape:

**Array of entries** (minimal fields only):

```json
[
  {
    "title": "Find large files",
    "content": "du -ah . | sort -rh | head -20",
    "tags": ["shell", "linux"],
    "priority": "medium"
  }
]
```

**Vault-shaped object**:

```json
{
  "entries": [
    {
      "title": "Python venv",
      "content": "python -m venv .venv && source .venv/bin/activate",
      "tags": ["python", "setup"],
      "priority": "high"
    }
  ]
}
```

Import assigns new UUIDs and timestamps to imported entries. Use `--dry-run` to validate without modifying the vault.

Sample files: [`examples/data/`](../examples/data/).

## Export format

### JSON

`stash export json` writes a JSON array of all entries (same field shape as stored in the vault).

### Markdown

`stash export markdown` writes a human-readable document with headings per entry, tags, priority, and content blocks.

## Filtering and sorting

`entry list` filter semantics:

| Filter | Behavior |
|--------|----------|
| `tag` / `tags` | Entry must have **all** specified tags |
| `priority` | Exact match |
| `since` / `until` | Filter by `created_at` range |
| `limit` | Cap number of results |
| `sort` | `newest`, `oldest`, or `title` |

Search matches against title, content, URL, and tag names (case-insensitive substring).
