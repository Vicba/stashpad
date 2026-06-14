"""Search vault entries."""

from __future__ import annotations

from typing import Optional

import typer
from pydantic import ValidationError as PydanticValidationError

from stash_cli.context import get_ctx
from stash_cli.exceptions import StashError, ValidationError
from stash_cli.output import emit_json, entry_summary, print_entry_table
from stash_cli.schemas import SearchQuery


def search(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Search query"),
    limit: int = typer.Option(20, "--limit", "-l", min=1),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Prompt for query"),
) -> None:
    """Search entries by title, content, URL, or tags.

    Parameters
    ----------
    ctx : typer.Context
        Typer context.
    query : str, optional
        Search string positional argument.
    limit : int
        Maximum number of results.
    interactive : bool
        Prompt for query when omitted.

    Returns
    -------
    None

    Examples
    --------
    $ stash search "docker prune"
    $ stash search --interactive
    """
    app_ctx = get_ctx(ctx)

    if interactive or query is None:
        query = typer.prompt("Search query")

    try:
        search_query = SearchQuery(query=query, limit=limit)
        results = app_ctx.storage.search(search_query)
        if app_ctx.json_output:
            emit_json([entry_summary(entry) for entry in results])
        elif not results:
            typer.echo(f"No results for '{search_query.query}'.")
        else:
            print_entry_table(results, title=f"Search: {search_query.query}")
    except (StashError, PydanticValidationError) as exc:
        message = exc.message if isinstance(exc, StashError) else str(exc)
        typer.echo(message, err=True)
        code = exc.exit_code if isinstance(exc, StashError) else ValidationError.exit_code
        raise typer.Exit(code=code) from exc
