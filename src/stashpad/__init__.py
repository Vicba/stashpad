"""Stash — personal developer reference manager."""

__version__ = "0.1.0"
__author__ = "Victor Barra"
__email__ = "victor.barra@live.be"

from stashpad.config import get_config, get_settings
from stashpad.models import Entry, Priority, Vault
from stashpad.schemas import EntryCreate, EntryFilter, EntryUpdate, SearchQuery
from stashpad.storage import VaultStorage

__all__ = [
    "Entry",
    "EntryCreate",
    "EntryFilter",
    "EntryUpdate",
    "Priority",
    "SearchQuery",
    "Vault",
    "VaultStorage",
    "__author__",
    "__email__",
    "__version__",
    "get_config",
    "get_settings",
]
