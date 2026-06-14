"""Domain models for the Stash vault."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from stash_cli.validators import normalize_tag_list, validate_http_url


def _utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Priority(str, Enum):
    """Entry priority level.

    Examples
    --------
    >>> Priority.HIGH.value
    'high'
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExportFormat(str, Enum):
    """Supported export formats.

    Examples
    --------
    >>> ExportFormat.JSON.value
    'json'
    """

    JSON = "json"
    MARKDOWN = "markdown"


class SortOrder(str, Enum):
    """Sort order for listing entries.

    Examples
    --------
    >>> SortOrder.NEWEST.value
    'newest'
    """

    NEWEST = "newest"
    OLDEST = "oldest"
    TITLE = "title"


class Entry(BaseModel):
    """A saved developer reference (snippet, command, URL, or note).

    Parameters
    ----------
    id : UUID
        Unique entry identifier; auto-generated if omitted.
    title : str
        Short label for the entry.
    content : str
        Body text: command, snippet, or note.
    url : str, optional
        Related http(s) URL.
    tags : list of str
        Normalized lowercase tags.
    priority : Priority
        Importance level.
    created_at : datetime
        Creation timestamp (UTC).
    updated_at : datetime
        Last modification timestamp (UTC).

    Examples
    --------
    >>> entry = Entry(title="Git undo", content="git reset --soft HEAD~1", tags=["git"])
    >>> entry.title
    'Git undo'
    """

    model_config = ConfigDict(use_enum_values=False)

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1)
    content: str
    url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        """Strip whitespace from title."""
        return value.strip()

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: Optional[str]) -> Optional[str]:
        """Ensure URL uses http or https."""
        return validate_http_url(value)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: List[str]) -> List[str]:
        """Normalize tag names."""
        return normalize_tag_list(value)


class VaultMetadata(BaseModel):
    """Metadata about the vault itself.

    Parameters
    ----------
    name : str
        Human-readable vault name.
    created_at : datetime
        When the vault was created (UTC).
    version : str
        Vault schema version string.

    Examples
    --------
    >>> VaultMetadata(name="work")
    VaultMetadata(name='work', created_at=..., version='1')
    """

    name: str = Field(default="default", min_length=1)
    created_at: datetime = Field(default_factory=_utc_now)
    version: str = "1"


class Vault(BaseModel):
    """The full vault: entries and known tags.

    Parameters
    ----------
    metadata : VaultMetadata
        Vault-level metadata.
    entries : list of Entry
        Stored reference entries.
    tags : list of str
        Registry of known tag names.

    Examples
    --------
    >>> vault = Vault()
    >>> vault.metadata.name
    'default'
    """

    metadata: VaultMetadata = Field(default_factory=VaultMetadata)
    entries: List[Entry] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
