"""Test Stash FastAPI endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from stash_cli.api import app, storage
from stash_cli.schemas import VaultInitOptions


@pytest.fixture
def client(tmp_path, monkeypatch):
    """API client with isolated vault."""
    data_dir = tmp_path / "api-vault"
    monkeypatch.setenv("STASH_DATA_DIR", str(data_dir))
    storage.data_dir = data_dir
    storage.vault_file = data_dir / storage.VAULT_FILENAME
    storage.initialize(VaultInitOptions(name="api-test"))
    return TestClient(app)


def test_health(client) -> None:
    """Health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_and_list_entries(client) -> None:
    """POST /entries and GET /entries work."""
    create = client.post(
        "/entries",
        json={"title": "API note", "content": "curl example", "tags": ["http"]},
    )
    assert create.status_code == 201
    entry_id = create.json()["id"]

    listing = client.get("/entries")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(f"/entries/{entry_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "API note"


def test_search(client) -> None:
    """GET /search finds entries."""
    client.post("/entries", json={"title": "Redis", "content": "SET key val"})
    response = client.get("/search", params={"q": "redis"})
    assert response.status_code == 200
    assert len(response.json()) == 1
