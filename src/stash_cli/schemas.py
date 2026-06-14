"""Pydantic request/response and filter schemas for Stash."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

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
    EntryCreate(title='Docker prune', content='docker system prune -af', url=None, tags=['devops'], priority=<Priority.MEDIUM: 'medium'>)
    """

    title: str = Field(min_length=1, description="Entry title")
    content: str = Field(description="Entry body content")
    url: Optional[str] = Field(default=None, description="Optional http(s) URL")
    tags: List[str] = Field(default_factory=list, description="Tag labels")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        """Strip whitespace from title."""
        return value.strip()

    @field_validator("url")
    @classmethod
    def check_url(cls, value: Optional[str]) -> Optional[str]:
        """Ensure URL uses http or https."""
        return validate_http_url(value)

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value: List[str]) -> List[str]:
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

    title: Optional[str] = Field(default=None, min_length=1)
    content: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[Priority] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: Optional[str]) -> Optional[str]:
        """Strip whitespace from title when provided."""
        return value.strip() if value is not None else None

    @field_validator("url")
    @classmethod
    def check_url(cls, value: Optional[str]) -> Optional[str]:
        """Ensure URL uses http or https when provided."""
        return validate_http_url(value)

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value: Optional[List[str]]) -> Optional[List[str]]:
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
    EntryFilter(tags=['python'], priority=None, since=None, until=None, limit=10, sort=<SortOrder.NEWEST: 'newest'>)
    """

    tags: Optional[List[str]] = None
    priority: Optional[Priority] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: Optional[int] = Field(default=None, ge=1)
    sort: SortOrder = SortOrder.NEWEST

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value: Optional[List[str]]) -> Optional[List[str]]:
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
    limit: Optional[int] = Field(default=20, ge=1)


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
    ImportPayload(entries=[EntryCreate(title='T', content='C', url=None, tags=[], priority=<Priority.MEDIUM: 'medium'>)])
    """

    entries: List[EntryCreate]

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
        ImportPayload(entries=[EntryCreate(title='A', content='B', url=None, tags=[], priority=<Priority.MEDIUM: 'medium'>)])
        """
        if isinstance(data, dict) and "entries" in data:
            raw_entries = data["entries"]
        elif isinstance(data, list):
            raw_entries = data
        else:
            raise ValueError("Import file must be a list of entries or a vault object")
        if not isinstance(raw_entries, list):
            raise ValueError("Import file entries must be a list")
        return cls(entries=[EntryCreate.model_validate(item) for item in raw_entries])


class HealthResponse(BaseModel):
    """API health check response."""

    status: str
    version: str
    app_name: str


class RootResponse(BaseModel):
    """API root endpoint response."""

    message: str
    version: str
    docs: str


class TagsResponse(BaseModel):
    """Response wrapper for tag lists."""

    tags: List[str]
    prefix: Optional[str] = None


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
    tag_prefix: Optional[str] = None
