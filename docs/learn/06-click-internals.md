# Click Internals

- **Docs:** [Vendored Click](https://typer.tiangolo.com/tutorial/vendored-click/)

Typer is built on [Click](https://click.palletsprojects.com/). Understanding this helps when debugging or extending CLIs.

## What Typer adds over Click

- Type hints drive argument/option parsing
- Automatic `--help` from docstrings
- Better editor autocomplete

## Where Click appears in Stash

Typer delegates to Click under the hood. You rarely import Click directly, but:

- `typer.confirm()` wraps Click's confirmation
- Exit handling uses `typer.Exit` (Click's `click.Exit`)
- Autocompletion callbacks follow Click's `(ctx, args, incomplete)` signature

## When to reach for Click directly

Use Click types when Typer doesn't expose what you need:

```python
import click

typer.prompt("Choose", type=click.Choice(["a", "b", "c"]))
```

See `init.py` for password confirmation patterns that combine Typer options with Click behavior.

## Further reading

- [Typer vs Click comparison](https://typer.tiangolo.com/alternatives/)
- [Click documentation](https://click.palletsprojects.com/en/stable/)
