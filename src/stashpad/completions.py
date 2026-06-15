"""Shell autocompletion helpers.

Typer chapter: CLI Option autocompletion — https://typer.tiangolo.com/tutorial/options-autocompletion/
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import typer

from stashpad.config import default_data_dir
from stashpad.context import AppContext
from stashpad.models import ExportFormat
from stashpad.storage import VaultStorage


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


def _resolve_data_dir(ctx: typer.Context) -> Path:
    """Read data directory from context or fall back to default."""
    if ctx.obj is not None and isinstance(ctx.obj, AppContext):
        return cast(Path, ctx.obj.storage.data_dir)
    return default_data_dir()
