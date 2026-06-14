# Daily workflow

A typical day using Stash to capture things you look up repeatedly.

## Morning: capture yesterday's lookups

```bash
# Something you googled twice — save it once
stash entry add \
  "Fix npm permissions" \
  "mkdir ~/.npm-global && npm config set prefix ~/.npm-global" \
  --tag node --tag setup

# Interactive mode when you don't have args ready
stash entry add --interactive
```

## During work: search before googling again

```bash
stash search "npm permissions"
stash entry list --tag node
stash entry ls --tags node,setup    # comma-separated filter
```

## End of day: quick review

```bash
stash entry list --since 2025-01-01 --sort newest --limit 10
stash tags list
```

## Open a saved URL in the browser

```bash
# Copy ID from `stash entry list`, then:
stash open <entry-uuid>
```

## Tips

- Use `--priority high` for commands you need every week.
- Use `--tag` repeatedly or `--tags a,b,c` for flexible filtering.
- Add `--json` when piping into `jq` or other tools.
