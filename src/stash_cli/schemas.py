"""Pydantic request/response and filter schemas for Stash."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from stash_cli.models import Priority, SortOrder
from stash_cli.validators import normalize_tag_list, validate_http_url


class EntryCreate(BaseModel):
    """Schema for creating a new vault entry.

    Parameters
    ----------
    title : str
        Short label shown in lists and search results.
    content : str
        Body text: command, snippet, or note.
    url : str, optional
        Related http(s) URL.
    tags : list of str, optional
        Labels for filtering; normalized to lowercase.
    priority : Priority, optional
        Entry importance; defaults to ``medium``.

    Examples
    --------
    >>> EntryCreate(title="Docker prune", content="docker system prune -af", tags=["devops"])
    EntryCreate(title='Docker prune', ...)
    """

    title: str = Field(min_length=1, description="Entry title")
    content: str = Field(description="Entry body content")
    url: str | None = Field(default=None, description="Optional http(s) URL")
    tags: list[str] = Field(default_factory=list, description="Tag labels")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        """Strip whitespace from title."""
        return value.strip()

    @field_validator("url")
    @classmethod
    def check_url(cls, value: str | None) -> str | None:
        """Ensure URL uses http or https."""
        return validate_http_url(value)

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value: list[str]) -> list[str]:
        """Normalize tag names."""
        return normalize_tag_list(value)


class EntryUpdate(BaseModel):
    """Schema for partial entry updates.

    Only fields that are set (not ``None``) are applied.

    Parameters
    ----------
    title : str, optional
        New title.
    content : str, optional
        New body content.
    url : str, optional
        New URL.
    tags : list of str, optional
        Replacement tag list.
    priority : Priority, optional
        New priority.

    Examples
    --------
    >>> EntryUpdate(title="Updated title")
    EntryUpdate(title='Updated title', content=None, url=None, tags=None, priority=None)
    """

    title: str | None = Field(default=None, min_length=1)
    content: str | None = None
    url: str | None = None
    tags: list[str] | None = None
    priority: Priority | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        """Strip whitespace from title when provided."""
        return value.strip() if value is not None else None

    @field_validator("url")
    @classmethod
    def check_url(cls, value: str | None) -> str | None:
        """Ensure URL uses http or https when provided."""
        return validate_http_url(value)

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value: list[str] | None) -> list[str] | None:
        """Normalize tag names when provided."""
        return normalize_tag_list(value) if value is not None else None


class EntryFilter(BaseModel):
    """Schema for filtering and sorting entry lists.

    Parameters
    ----------
    tags : list of str, optional
        Require all listed tags on each entry.
    priority : Priority, optional
        Filter by priority level.
    since : datetime, optional
        Include entries created on or after this time.
    until : datetime, optional
        Include entries created on or before this time.
    limit : int, optional
        Maximum number of results (>= 1).
    sort : SortOrder, optional
        Sort order; defaults to newest first.

    Examples
    --------
    >>> EntryFilter(tags=["python"], limit=10)
    EntryFilter(tags=['python'], ...)
    """

    tags: list[str] | None = None
    priority: Priority | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int | None = Field(default=None, ge=1)
    sort: SortOrder = SortOrder.NEWEST

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value: list[str] | None) -> list[str] | None:
        """Normalize filter tags."""
        return normalize_tag_list(value) if value else None


class SearchQuery(BaseModel):
    """Schema for search requests.

    Parameters
    ----------
    query : str
        Case-insensitive search string.
    limit : int, optional
        Maximum results; defaults to 20.

    Examples
    --------
    >>> SearchQuery(query="docker")
    SearchQuery(query='docker', limit=20)
    """

    query: str = Field(min_length=1, description="Search text")
    limit: int | None = Field(default=20, ge=1)


class VaultInitOptions(BaseModel):
    """Schema for vault initialization.

    Parameters
    ----------
    name : str, optional
        Display name for the vault; defaults to ``default``.

    Examples
    --------
    >>> VaultInitOptions(name="work")
    VaultInitOptions(name='work')
    """

    name: str = Field(default="default", min_length=1)


class ImportPayload(BaseModel):
    """Schema for validating JSON import files.

    Accepts either a bare list of entries or a vault-shaped object.

    Parameters
    ----------
    entries : list of EntryCreate
        Entries to import.

    Examples
    --------
    >>> ImportPayload(entries=[EntryCreate(title="T", content="C")])
    ImportPayload(entries=[EntryCreate(title='T', ...)])
    """

    entries: list[EntryCreate]

    @classmethod
    def from_raw(cls, data: object) -> ImportPayload:
        """Build payload from parsed JSON (list or vault dict).

        Parameters
        ----------
        data : object
            Parsed JSON: list of entry dicts or ``{"entries": [...]}``.

        Returns
        -------
        ImportPayload
            Validated import payload.

        Raises
        ------
        ValueError
            If the JSON shape is not supported.

        Examples
        --------
        >>> ImportPayload.from_raw([{"title": "A", "content": "B"}])
        ImportPayload(entries=[EntryCreate(title='A', ...)])
        """
        if isinstance(data, dict) and "entries" in data:
            raw_entries = data["entries"]
        elif isinstance(data, list):
            raw_entries = data
        else:
            msg = "Import file must be a list of entries or a vault object"
            raise ValueError(msg)
        if not isinstance(raw_entries, list):
            msg = "Import file entries must be a list"
            raise TypeError(msg)
        return cls(entries=[EntryCreate.model_validate(item) for item in raw_entries])


class AppContextSchema(BaseModel):
    """Shared CLI context passed via ``ctx.obj``.

    Parameters
    ----------
    verbose : bool
        Enable verbose logging output.
    json_output : bool
        Emit JSON instead of Rich formatting.
    storage : VaultStorage
        Vault persistence handle.
    tag_prefix : str, optional
        Tag prefix filter for tag subcommands.

    Notes
    -----
    ``storage`` is a runtime object; Pydantic allows it via
    ``arbitrary_types_allowed``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    verbose: bool = False
    json_output: bool = False
    storage: object
    tag_prefix: str | None = None
