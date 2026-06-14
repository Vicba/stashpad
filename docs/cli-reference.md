# CLI reference

All commands are invoked as `stash [global options] <command> …`.

Run `stash --help` or `stash <command> --help` for built-in usage text.

## Global options

| Flag | Short | Description |
|------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output |
| `--json` | | Emit JSON instead of formatted tables |
| `--config-dir PATH` | | Override vault data directory (also `STASH_DATA_DIR`) |
| `--version` | | Print version and exit |

Example:

```bash
stash --json --config-dir /tmp/demo-vault entry list
```

---

## `stash init`

Create and initialize a new vault.

| Argument / option | Description |
|-------------------|-------------|
| `[data_dir]` | Vault directory (default: `STASH_DATA_DIR` or `~/.config/stash`) |
| `--name`, `-n` | Vault display name (prompts if omitted) |
| `--force`, `-f` | Re-initialize even if vault already exists |

```bash
stash init --name work
stash init /path/to/vault --name team --force
```

---

## `stash entry`

Manage vault entries. Alias group: `entry`.

### `stash entry add`

| Argument / option | Description |
|-------------------|-------------|
| `TITLE` | Entry title (required) |
| `CONTENT` | Body: command, snippet, or note (required) |
| `--url`, `-u` | Related http(s) URL |
| `--tag`, `-t` | Tag (repeatable) |
| `--tags` | Comma-separated tags (`work,python,docker`) |
| `--priority`, `-p` | `low`, `medium`, or `high` (default: `medium`) |
| `--interactive`, `-i` | Prompt for missing fields |

```bash
stash entry add "Poetry install" "poetry install" --tag python --priority high
```

### `stash entry list` / `stash entry ls`

| Option | Description |
|--------|-------------|
| `--tag`, `-t` | Filter by tag (repeatable; all must match) |
| `--tags` | Comma-separated required tags |
| `--priority`, `-p` | Filter by priority |
| `--since` | Entries created on or after date (`YYYY-MM-DD` or ISO datetime) |
| `--until` | Entries created on or before date |
| `--limit`, `-l` | Maximum results (default: 50) |
| `--sort` | `newest`, `oldest`, or `title` (default: `newest`) |

```bash
stash entry list --tag devops --limit 10
stash entry ls --tags python,cli --sort title
```

### `stash entry show`

| Argument | Description |
|----------|-------------|
| `ENTRY_ID` | Entry UUID |

### `stash entry edit`

| Argument / option | Description |
|-------------------|-------------|
| `ENTRY_ID` | Entry UUID |
| `--title` | New title (required) |
| `--content`, `-c` | New body |
| `--url`, `-u` | New URL |
| `--tags` | Comma-separated replacement tags |
| `--priority`, `-p` | New priority |

```bash
stash entry edit <uuid> --title "Updated title" --content "new body"
```

### `stash entry remove` / `stash entry rm`

| Argument / option | Description |
|-------------------|-------------|
| `ENTRY_ID …` | One or more entry UUIDs |
| `--force`, `-F` | Skip confirmation |

```bash
stash entry rm <uuid1> <uuid2> --force
```

---

## `stash search`

Full-text search across title, content, URL, and tags.

| Argument / option | Description |
|-------------------|-------------|
| `QUERY` | Search string (optional if `--interactive`) |
| `--limit`, `-l` | Maximum results (default: 20) |
| `--interactive`, `-i` | Prompt for query |

```bash
stash search "docker prune"
stash search --interactive
```

---

## `stash tags`

Manage the tag registry. Shared group option:

| Option | Description |
|--------|-------------|
| `--prefix`, `-p` | Filter tags by prefix (applies to all tag subcommands) |

### `stash tags list`

List known tags (optionally filtered by `--prefix`).

### `stash tags add`

Register a tag name in the vault without attaching it to an entry.

### `stash tags remove`

| Argument / option | Description |
|-------------------|-------------|
| `TAG` | Tag name to remove from registry |
| `--force`, `-f` | Skip confirmation |

---

## `stash export`

Export vault entries to a file.

### `stash export json`

| Argument / option | Description |
|-------------------|-------------|
| `OUTPUT` | Output file path |
| `--all` / `--filtered` | Export all entries (default: `--all`) |

### `stash export markdown`

Same options as `export json`; writes a Markdown document.

```bash
stash export json ./backup.json
stash export markdown ./notes.md
```

---

## `stash import`

Import entries from JSON file(s).

| Option | Description |
|--------|-------------|
| `--from-file`, `-f` | Single JSON file |
| `--directory`, `-d` | Directory of `*.json` files |
| `--dry-run` | Validate without writing to vault |

One of `--from-file` or `--directory` is required.

```bash
stash import --from-file ./backup.json
stash import --directory ./exports/ --dry-run
```

See [Data model](data-model.md#import-format) for accepted JSON shapes.

---

## `stash open`

Open an entry's URL in the default system browser.

| Argument | Description |
|----------|-------------|
| `ENTRY_ID` | Entry UUID (must have a `url` field) |

---

## `stash config`

View configuration. Settings are loaded from environment variables and `.env`.

### `stash config show`

Print all current settings.

### `stash config path`

Print the vault data directory path.

### `stash config set`

| Option | Description |
|--------|-------------|
| `--key`, `-k` | Setting name (required) |
| `--value`, `-v` | Setting value (prompts if omitted) |

Prints guidance to add `STASH_<KEY>=<value>` to your `.env` file. See [Configuration](configuration.md).

---

## Shell autocompletion

Tag names autocomplete on `--tag` options where supported. Install completion for your shell using Typer's standard completion mechanism:

```bash
stash --install-completion
```

Run `stash --show-completion` for the completion script source.
