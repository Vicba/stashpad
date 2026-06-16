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
| `CONTENT` | Body: command, snippet, or note; use `-` for stdin |
| `--clipboard` | Read body from the system clipboard |
| `--from-stdin` | Read body from stdin (same as `-`) |
| `--url`, `-u` | Related http(s) URL |
| `--tag`, `-t` | Tag (repeatable) |
| `--tags` | Comma-separated tags (`work,python,docker`) |
| `--priority`, `-p` | `low`, `medium`, or `high` (default: `medium`) |
| `--interactive`, `-i` | Prompt for missing fields |
| `--pin` | Pin entry for quick access via `stash pins` |
| `--kind` | Entry type: `command`, `url`, `snippet`, or `note` (inferred when omitted) |

```bash
stash entry add "Poetry install" "poetry install" --tag python --priority high
stash entry add "Internal docs" --url https://wiki.example.com --kind url
stash entry add "Recent commits" -
git log --oneline -5 | stash entry add "Recent commits" -
stash entry add "Snippet" --clipboard
stash add "Quick note" "echo hello"    # top-level alias
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
| `--pinned` | Show only pinned entries |
| `--kind` | Filter by entry kind |

```bash
stash entry list --tag devops --limit 10
stash entry list --pinned
stash entry ls --tags python,cli --sort title
```

### `stash entry pin` / `stash entry unpin`

| Argument | Description |
|----------|-------------|
| `ENTRY_ID` | Entry UUID |

```bash
stash entry pin <uuid>
stash entry unpin <uuid>
```

### `stash pins`

List pinned favorites — daily go-to commands, deploy scripts, and URLs. Default limit is 10, sorted by title.

| Option | Description |
|--------|-------------|
| `--limit`, `-l` | Maximum results (default: 10) |
| `--sort` | `newest`, `oldest`, or `title` (default: `title`) |

```bash
stash pins
stash pins --limit 20
```

### `stash pick`

Interactive picker — searchable list of entries. Uses **fzf** when installed; falls back to a numbered list otherwise. Default action is **copy** when no action flag is given.

| Argument / option | Description |
|-------------------|-------------|
| `[QUERY]` | Optional initial fuzzy filter |
| `--copy` | Copy the selected entry (commands copy first line by default) |
| `--run` | Run the selected entry (commands only) |
| `--open` | Open the selected entry in a browser (url entries only) |
| `--first-line`, `-1` | Copy or run only the first non-empty line |
| `--force`, `-F` | Skip run confirmation |
| `--pinned` | Only pinned entries |
| `--kind` | Filter by entry kind |
| `--tag`, `-t` / `--tags` | Tag filters |
| `--limit`, `-l` | Maximum candidates (default: 100) |
| `--exact` | Disable fuzzy matching |

```bash
stash pick
stash pick deploy --copy
stash pick --run --pinned
alias sp='stash pick --copy'    # shell alias
```

### `stash browse`

Split-pane terminal UI for exploring vault entries. Toggle tag filters on the left
to narrow the list — select multiple tags to show entries with **any** of them (OR logic).
Requires the optional TUI extra:

```bash
poetry install -E tui
```

| Argument / option | Description |
|-------------------|-------------|
| `[QUERY]` | Optional initial fuzzy filter |
| `--pinned` | Only pinned entries |
| `--kind` | Filter by entry kind |
| `--tag`, `-t` / `--tags` | Tag filters |
| `--limit`, `-l` | Maximum candidates (default: 100) |
| `--exact` | Disable fuzzy matching |
| `--first-line`, `-1` | Copy or run only the first non-empty line |
| `--force`, `-F` | Skip run confirmation |

**Keyboard shortcuts** (inside the TUI):

| Key | Action |
|-----|--------|
| `t` | Focus tag filters |
| `Space` / `Enter` | Toggle the highlighted tag filter on or off |
| `l` | Focus entry list |
| `/` | Focus search |
| `c` | Copy selected entry |
| `o` | Open URL (url entries only) |
| `r` | Run command (command entries only) |
| `d` | Delete selected entry (with confirmation) |
| `q` | Quit |

Tag filters appear **above the search bar** in the browse column. Select multiple tags
(e.g. `devops` + `k8s`) to show entries that have **any** selected tag. Choose
**All entries** to clear tag filters. **Untagged** is exclusive.
On narrow terminals the preview moves below the list; tag filters stay visible.

```bash
stash browse
stash browse deploy --tag devops
stash --config-dir /path/to/vault browse --pinned
```

### `stash entry show`

| Argument | Description |
|----------|-------------|
| `ENTRY_ID` | Entry UUID |

### `stash entry copy`

Copy entry content to the system clipboard. URL entries copy the URL; other kinds copy content.

| Argument / option | Description |
|-------------------|-------------|
| `ENTRY_ID` | Entry UUID |
| `--first-line`, `-1` | Copy only the first non-empty line (the command) |

```bash
stash entry copy <uuid>
stash entry copy <uuid> --first-line
stash --json entry copy <uuid>   # {"copied": "...", "id": "...", "first_line": false}
```

### `stash entry run`

Execute entry content in the shell. **Only `command` entries** can be run. Prompts for confirmation unless `--force` is set. Propagates the subprocess exit code.

| Argument / option | Description |
|-------------------|-------------|
| `ENTRY_ID` | Entry UUID |
| `--first-line`, `-1` | Run only the first non-empty line (the command) |
| `--force`, `-F` | Skip confirmation |

```bash
stash entry run <uuid>
stash entry run <uuid> --first-line --force
```

### `stash entry edit`

| Argument / option | Description |
|-------------------|-------------|
| `ENTRY_ID` | Entry UUID |
| `--title` | New title (required) |
| `--content`, `-c` | New body |
| `--url`, `-u` | New URL |
| `--tags` | Comma-separated replacement tags |
| `--priority`, `-p` | New priority |
| `--pin` / `--unpin` | Pin or unpin the entry |
| `--kind` | New entry type |

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

Fuzzy, ranked search across title, content, URL, and tags. Results are scored by
text relevance, then boosted by priority, recency (`updated_at`), and how
recently the entry was opened (`opened_at` is set by `entry show`, `entry copy`,
`entry run`, and `open`).

Fuzzy matching uses subsequence search — e.g. `prn` matches **Docker prune**.
Use `--exact` to require literal substring matches only.

| Argument / option | Description |
|-------------------|-------------|
| `QUERY` | Search string (optional if `--interactive`) |
| `--limit`, `-l` | Maximum results (default: 20) |
| `--interactive`, `-i` | Prompt for query |
| `--exact` | Disable fuzzy matching |

```bash
stash search "docker prune"
stash search prn                    # fuzzy: matches "Docker prune"
stash search prn --exact            # no fuzzy match
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

Open a **`url` entry** in the default system browser. Commands with a supplementary docs link must use `kind command`; only `kind url` entries can be opened.

| Argument | Description |
|----------|-------------|
| `ENTRY_ID` | Entry UUID (must be `kind: url` with a `url` field) |

```bash
stash entry add "Wiki" --url https://wiki.example.com --kind url
stash open <uuid>
```

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
