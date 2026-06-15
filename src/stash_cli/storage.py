"""Vault persistence layer.

Typer chapter: CLI Application Directory — https://typer.tiangolo.com/tutorial/app-dir/
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError as PydanticValidationError

from stash_cli.constants import DEFAULT_SEARCH_LIMIT, VAULT_FILENAME
from stash_cli.exceptions import (
    EntryNotFoundError,
    StorageError,
    VaultNotInitializedError,
)
from stash_cli.models import Entry, SortOrder, Vault, VaultMetadata
from stash_cli.schemas import EntryCreate, EntryFilter, EntryUpdate, SearchQuery, VaultInitOptions
from stash_cli.search_rank import rank_search_results
from stash_cli.validators import normalize_tag_list

if TYPE_CHECKING:
    from uuid import UUID


class VaultStorage:
    """Read and write vault data as JSON on disk.

    Parameters
    ----------
    data_dir : Path
        Directory where ``vault.json`` is stored.

    Examples
    --------
    >>> from pathlib import Path
    >>> from stash_cli.schemas import VaultInitOptions
    >>> s = VaultStorage(Path("/tmp/stash-demo"))
    >>> s.initialize(VaultInitOptions(name="demo")).metadata.name
    'demo'
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize storage for a given data directory.

        Parameters
        ----------
        data_dir : Path
            Root directory for vault files.
        """
        self.data_dir = Path(data_dir)
        self.vault_file = self.data_dir / VAULT_FILENAME

    @property
    def is_initialized(self) -> bool:
        """Check whether the vault file exists on disk.

        Returns
        -------
        bool
            ``True`` if ``vault.json`` is present.
        """
        return self.vault_file.is_file()

    def ensure_data_dir(self) -> None:
        """Create the data directory if it does not exist.

        Returns
        -------
        None
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self, options: VaultInitOptions | None = None) -> Vault:
        """Create a new empty vault and persist it.

        Parameters
        ----------
        options : VaultInitOptions, optional
            Initialization options; defaults to name ``default``.

        Returns
        -------
        Vault
            The newly created vault.

        Examples
        --------
        >>> from pathlib import Path
        >>> from stash_cli.schemas import VaultInitOptions
        >>> s = VaultStorage(Path("/tmp/stash-init-demo"))
        >>> s.initialize(VaultInitOptions(name="work")).metadata.name
        'work'
        """
        opts = options or VaultInitOptions()
        self.ensure_data_dir()
        vault = Vault(metadata=VaultMetadata(name=opts.name))
        self.save(vault)
        return vault

    def require_vault(self) -> Vault:
        """Load the vault or raise if not initialized.

        Returns
        -------
        Vault
            Loaded vault data.

        Raises
        ------
        VaultNotInitializedError
            If ``vault.json`` does not exist.
        """
        if not self.is_initialized:
            msg = "Vault not initialized. Run 'stash init' first."
            raise VaultNotInitializedError(msg)
        return self.load()

    def load(self) -> Vault:
        """Load vault from disk.

        Returns
        -------
        Vault
            Parsed vault, or empty vault if file is missing.

        Raises
        ------
        StorageError
            If the file cannot be read or parsed.
        """
        if not self.is_initialized:
            return Vault()
        try:
            raw = self.vault_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            return Vault.model_validate(data)
        except (OSError, json.JSONDecodeError, PydanticValidationError) as exc:
            msg = f"Failed to load vault: {exc}"
            raise StorageError(msg) from exc

    def save(self, vault: Vault) -> None:
        """Atomically write vault to disk.

        Parameters
        ----------
        vault : Vault
            Vault model to persist.

        Raises
        ------
        StorageError
            If writing fails.
        """
        self.ensure_data_dir()
        payload = vault.model_dump(mode="json")
        try:
            fd, tmp_path = tempfile.mkstemp(
                dir=self.data_dir,
                prefix=".vault-",
                suffix=".tmp",
            )
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            Path(tmp_path).replace(self.vault_file)
        except OSError as exc:
            msg = f"Failed to save vault: {exc}"
            raise StorageError(msg) from exc

    def add_entry(self, data: EntryCreate) -> Entry:
        """Add a new entry to the vault.

        Parameters
        ----------
        data : EntryCreate
            Validated entry creation payload.

        Returns
        -------
        Entry
            The persisted entry including generated id and timestamps.

        Examples
        --------
        >>> from pathlib import Path
        >>> from stash_cli.schemas import EntryCreate, VaultInitOptions
        >>> s = VaultStorage(Path("/tmp/stash-add-demo"))
        >>> _ = s.initialize(VaultInitOptions())
        >>> s.add_entry(EntryCreate(title="T", content="C")).title
        'T'
        """
        vault = self.require_vault()
        entry = Entry.model_validate(data.model_dump())
        vault.entries.append(entry)
        self._merge_tags(vault, entry.tags)
        self.save(vault)
        return entry

    def get_entry(self, entry_id: UUID) -> Entry:
        """Return a single entry by ID.

        Parameters
        ----------
        entry_id : UUID
            Entry identifier.

        Returns
        -------
        Entry
            Matching entry.

        Raises
        ------
        EntryNotFoundError
            If no entry matches ``entry_id``.
        """
        vault = self.require_vault()
        for entry in vault.entries:
            if entry.id == entry_id:
                return entry
        msg = f"Entry '{entry_id}' not found"
        raise EntryNotFoundError(msg)

    def touch_entry(self, entry_id: UUID) -> Entry:
        """Record that an entry was viewed or used.

        Parameters
        ----------
        entry_id : UUID
            Entry identifier.

        Returns
        -------
        Entry
            Entry with ``opened_at`` set to now (UTC).
        """
        vault = self.require_vault()
        for entry in vault.entries:
            if entry.id == entry_id:
                entry.opened_at = datetime.now(timezone.utc)
                self.save(vault)
                return entry
        msg = f"Entry '{entry_id}' not found"
        raise EntryNotFoundError(msg)

    def update_entry(self, entry_id: UUID, data: EntryUpdate) -> Entry:
        """Update fields on an existing entry.

        Parameters
        ----------
        entry_id : UUID
            Entry to update.
        data : EntryUpdate
            Partial update; only set fields are applied.

        Returns
        -------
        Entry
            Updated entry.
        """
        vault = self.require_vault()
        for entry in vault.entries:
            if entry.id != entry_id:
                continue
            updates = data.model_dump(exclude_unset=True)
            for field, value in updates.items():
                setattr(entry, field, value)
            entry.updated_at = datetime.now(timezone.utc)
            if data.tags is not None:
                self._merge_tags(vault, entry.tags)
            self.save(vault)
            return entry
        msg = f"Entry '{entry_id}' not found"
        raise EntryNotFoundError(msg)

    def remove_entries(self, entry_ids: list[UUID]) -> int:
        """Remove one or more entries.

        Parameters
        ----------
        entry_ids : list of UUID
            IDs to delete.

        Returns
        -------
        int
            Number of entries removed.

        Raises
        ------
        EntryNotFoundError
            If none of the IDs match.
        """
        vault = self.require_vault()
        id_set = set(entry_ids)
        before = len(vault.entries)
        vault.entries = [entry for entry in vault.entries if entry.id not in id_set]
        removed = before - len(vault.entries)
        if removed == 0:
            msg = "No matching entries found"
            raise EntryNotFoundError(msg)
        self.save(vault)
        return removed

    def list_entries(self, filters: EntryFilter | None = None) -> list[Entry]:
        """Return filtered and sorted entries.

        Parameters
        ----------
        filters : EntryFilter, optional
            Filter and sort options; defaults to all entries, newest first.

        Returns
        -------
        list of Entry
            Matching entries.

        Examples
        --------
        >>> from pathlib import Path
        >>> from stash_cli.schemas import EntryFilter, VaultInitOptions
        >>> s = VaultStorage(Path("/tmp/stash-list-demo"))
        >>> _ = s.initialize(VaultInitOptions())
        >>> isinstance(s.list_entries(EntryFilter(limit=5)), list)
        True
        """
        filt = filters or EntryFilter()
        vault = self.require_vault()
        results = list(vault.entries)

        if filt.tags:
            tag_set = {tag.lower() for tag in filt.tags}
            results = [
                entry for entry in results if tag_set.issubset({t.lower() for t in entry.tags})
            ]

        if filt.priority is not None:
            results = [entry for entry in results if entry.priority == filt.priority]

        if filt.since is not None:
            results = [entry for entry in results if entry.created_at >= filt.since]

        if filt.until is not None:
            results = [entry for entry in results if entry.created_at <= filt.until]

        if filt.pinned is not None:
            results = [entry for entry in results if entry.pinned is filt.pinned]

        if filt.kind is not None:
            results = [entry for entry in results if entry.kind == filt.kind]

        if filt.sort == SortOrder.NEWEST:
            results.sort(key=lambda entry: entry.created_at, reverse=True)
        elif filt.sort == SortOrder.OLDEST:
            results.sort(key=lambda entry: entry.created_at)
        elif filt.sort == SortOrder.TITLE:
            results.sort(key=lambda entry: entry.title.lower())

        if filt.limit is not None:
            results = results[: filt.limit]

        return results

    def search(self, query: SearchQuery | str, limit: int | None = None) -> list[Entry]:
        """Search entries by title, content, tags, or URL.

        Parameters
        ----------
        query : SearchQuery or str
            Search text and optional limit.
        limit : int, optional
            Legacy limit when ``query`` is a plain string.

        Returns
        -------
        list of Entry
            Matching entries, newest first.

        Examples
        --------
        >>> from pathlib import Path
        >>> from stash_cli.schemas import SearchQuery, VaultInitOptions
        >>> s = VaultStorage(Path("/tmp/stash-search-demo"))
        >>> _ = s.initialize(VaultInitOptions())
        >>> s.search(SearchQuery(query="missing"))
        []
        """
        search = (
            SearchQuery(query=query, limit=limit or DEFAULT_SEARCH_LIMIT)
            if isinstance(query, str)
            else query
        )

        vault = self.require_vault()
        return rank_search_results(
            vault.entries,
            search.query,
            limit=search.limit,
            fuzzy=search.fuzzy,
        )

    def list_tags(self, prefix: str | None = None) -> list[str]:
        """Return known tags, optionally filtered by prefix.

        Parameters
        ----------
        prefix : str, optional
            Only tags starting with this prefix (case-insensitive).

        Returns
        -------
        list of str
            Sorted tag names.
        """
        vault = self.require_vault()
        tags = sorted(vault.tags)
        if prefix:
            prefix_lower = prefix.lower()
            tags = [tag for tag in tags if tag.lower().startswith(prefix_lower)]
        return tags

    def add_tag(self, tag: str) -> str:
        """Register a tag in the vault.

        Parameters
        ----------
        tag : str
            Tag name to add.

        Returns
        -------
        str
            Normalized tag string.
        """
        vault = self.require_vault()
        normalized = normalize_tag_list([tag])[0]
        self._merge_tags(vault, [normalized])
        self.save(vault)
        return normalized

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the registry (entries keep their tags).

        Parameters
        ----------
        tag : str
            Tag name to remove from the registry.
        """
        vault = self.require_vault()
        normalized = tag.strip().lower()
        vault.tags = [existing for existing in vault.tags if existing.lower() != normalized]
        self.save(vault)

    def merge_tags(self, vault: Vault, tags: list[str]) -> None:
        """Add tags to the vault registry if missing.

        Parameters
        ----------
        vault : Vault
            Vault to update in memory.
        tags : list of str
            Tags to register.
        """
        self._merge_tags(vault, tags)

    @staticmethod
    def _merge_tags(vault: Vault, tags: list[str]) -> None:
        """Merge tags into the vault registry."""
        existing = {tag.lower() for tag in vault.tags}
        for tag in tags:
            if tag.lower() not in existing:
                vault.tags.append(tag)
                existing.add(tag.lower())
