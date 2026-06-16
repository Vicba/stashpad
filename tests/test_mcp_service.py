"""Tests for VaultMcpService."""

from __future__ import annotations

import pytest

from stashpad.exceptions import ValidationError
from stashpad.mcp.service import (
    COUNT_KEY,
    ENTRIES_KEY,
    ENTRY_KEY,
    VaultMcpService,
)
from stashpad.schemas import EntryCreate, VaultInitOptions
from stashpad.storage import VaultStorage


def _vault_service(tmp_path) -> VaultMcpService:
    """Return a service backed by a fresh initialized vault."""
    storage = VaultStorage(tmp_path / "vault")
    storage.initialize(VaultInitOptions())
    return VaultMcpService(storage)


def test_search_entries_returns_ranked_matches(tmp_path) -> None:
    """Search returns matching entries with count."""
    service = _vault_service(tmp_path)
    service.storage.add_entry(EntryCreate(title="Docker prune", content="docker system prune -af"))
    service.storage.add_entry(EntryCreate(title="Python REPL", content="python"))

    result = service.search_entries("docker prune")

    assert result[COUNT_KEY] == 1
    assert result[ENTRIES_KEY][0]["title"] == "Docker prune"


def test_list_filtered_entries_applies_tag_filter(tmp_path) -> None:
    """List applies tag filters with AND semantics."""
    service = _vault_service(tmp_path)
    service.storage.add_entry(
        EntryCreate(title="Deploy", content="kubectl apply", tags=["devops", "k8s"]),
    )
    service.storage.add_entry(
        EntryCreate(title="REPL", content="python", tags=["python"]),
    )

    result = service.list_filtered_entries(tags=["devops"])

    assert result[COUNT_KEY] == 1
    assert result[ENTRIES_KEY][0]["title"] == "Deploy"


def test_fetch_entry_does_not_touch_opened_at(tmp_path) -> None:
    """Fetch is a pure read and leaves opened_at unchanged."""
    service = _vault_service(tmp_path)
    created = service.storage.add_entry(EntryCreate(title="Deploy", content="kubectl apply"))

    result = service.fetch_entry(str(created.id))
    stored = service.storage.get_entry(created.id)

    assert result[ENTRY_KEY]["title"] == "Deploy"
    assert stored.opened_at is None


def test_create_entry_infers_command_kind(tmp_path) -> None:
    """Create normalizes content and infers command kind."""
    service = _vault_service(tmp_path)

    result = service.create_entry(
        "Deploy",
        content="kubectl apply -f deploy.yaml",
        tags=["devops"],
    )

    assert result[ENTRY_KEY]["title"] == "Deploy"
    assert result[ENTRY_KEY]["kind"] == "command"
    assert result[ENTRY_KEY]["tags"] == ["devops"]


def test_create_entry_rejected_in_read_only_mode(tmp_path) -> None:
    """Read-only service rejects create operations."""
    service = VaultMcpService(_vault_service(tmp_path).storage, read_only=True)

    with pytest.raises(ValidationError, match="read-only"):
        service.create_entry("Blocked", content="echo nope")


def test_fetch_entry_rejects_invalid_uuid(tmp_path) -> None:
    """Fetch validates entry ID format."""
    service = _vault_service(tmp_path)

    with pytest.raises(ValidationError, match="Invalid entry ID"):
        service.fetch_entry("not-a-uuid")
