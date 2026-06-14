# API workflow

Use the REST API when a GUI, script, or another tool needs access to your vault.

## Start the API

```bash
poetry run poe api --dev
# Docs: http://localhost:8000/docs
```

## Create and list entries (curl)

```bash
# Create
curl -s -X POST http://localhost:8000/entries \
  -H "Content-Type: application/json" \
  -d '{"title":"Health check","content":"curl localhost:8000/health","tags":["api"]}' | jq

# List
curl -s http://localhost:8000/entries | jq

# Search
curl -s "http://localhost:8000/search?q=health" | jq
```

## CLI and API share the same vault

Both read from `~/.config/stash/vault.json` (or `STASH_DATA_DIR`):

```bash
stash entry add "From CLI" "added via terminal" --tag demo
curl -s http://localhost:8000/entries | jq '.[] | select(.title=="From CLI")'
```

## Health and config

```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/config | jq
```

The API uses the same Pydantic models as the CLI (`EntryCreate`, `EntryUpdate`, `EntryFilter`).
