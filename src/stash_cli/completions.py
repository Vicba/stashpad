"""Shell autocompletion helpers.

Typer chapter: CLI Option autocompletion — https://typer.tiangolo.com/tutorial/options-autocompletion/
"""

from __future__ import annotations

import typer

from stash_cli.config import default_data_dir
from stash_cli.context import AppContext
from stash_cli.models import ExportFormat
from stash_cli.storage import VaultStorage


def complete_tags(ctx: typer.Context, args: list[str], incomplete: str) -> list[str]:
    """Suggest tags from the vault for shell completion."""
    data_dir = _resolve_data_dir(ctx)
    storage = VaultStorage(data_dir)
    if not storage.is_initialized:
        return []
    tags = storage.list_tags(prefix=incomplete or None)
    return [tag for tag in tags if tag.startswith(incomplete)]


def complete_export_formats(ctx: typer.Context, args: list[str], incomplete: str) -> list[str]:
    """Suggest export format names."""
    return [fmt.value for fmt in ExportFormat if fmt.value.startswith(incomplete)]


def _resolve_data_dir(ctx: typer.Context):
    """Read data directory from context or fall back to default."""
    if ctx.obj is not None and isinstance(ctx.obj, AppContext):
        return ctx.obj.storage.data_dir
    return default_data_dir()
