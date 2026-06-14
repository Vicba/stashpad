"""Stash REST API — mirrors the CLI vault data model."""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

import coloredlogs
from fastapi import FastAPI, HTTPException, Query, Response

from stash_cli import __version__
from stash_cli.config import get_settings
from stash_cli.exceptions import EntryNotFoundError, StashError, VaultNotInitializedError
from stash_cli.models import Entry, Priority, SortOrder
from stash_cli.schemas import (
    EntryCreate,
    EntryFilter,
    EntryUpdate,
    HealthResponse,
    RootResponse,
    SearchQuery,
)
from stash_cli.storage import VaultStorage

app = FastAPI(
    title="Stash",
    description="Personal developer reference manager API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

storage = VaultStorage(get_settings().data_dir)


@app.on_event("startup")
def startup_event() -> None:
    """Configure colored logging on API startup.

    Returns
    -------
    None
    """
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    coloredlogs.install()


def _handle_error(exc: StashError) -> HTTPException:
    """Map ``StashError`` subclasses to HTTP status codes.

    Parameters
    ----------
    exc : StashError
        Domain exception from storage layer.

    Returns
    -------
    HTTPException
        FastAPI-compatible HTTP error.
    """
    status_map = {
        VaultNotInitializedError: 503,
        EntryNotFoundError: 404,
    }
    status = status_map.get(type(exc), 500)
    return HTTPException(status_code=status, detail=exc.message)


@app.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    """Return basic API metadata.

    Returns
    -------
    RootResponse
        Welcome message and docs link.
    """
    return RootResponse(
        message="Hello from Stash!",
        version=__version__,
        docs="/docs",
    )


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns
    -------
    HealthResponse
        Service health and version.
    """
    return HealthResponse(status="healthy", version=__version__, app_name="Stash")


@app.get("/config", response_model=dict)
def get_config_endpoint() -> dict:
    """Return application configuration as JSON.

    Returns
    -------
    dict
        Serialized ``Settings`` model.
    """
    settings = get_settings()
    return settings.model_dump(mode="json")


@app.post("/entries", response_model=Entry, status_code=201)
def create_entry(body: EntryCreate) -> Entry:
    """Create a new vault entry.

    Parameters
    ----------
    body : EntryCreate
        Validated entry payload.

    Returns
    -------
    Entry
        Created entry with generated id.
    """
    try:
        return storage.add_entry(body)
    except StashError as exc:
        raise _handle_error(exc) from exc


@app.get("/entries", response_model=List[Entry])
def list_entries(
    tag: Optional[List[str]] = Query(None),
    priority: Optional[Priority] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = Query(50, ge=1),
    sort: SortOrder = SortOrder.NEWEST,
) -> List[Entry]:
    """List entries with optional Pydantic filters.

    Parameters
    ----------
    tag : list of str, optional
        Required tags (all must match).
    priority : Priority, optional
        Filter by priority.
    since : str, optional
        ISO datetime lower bound.
    until : str, optional
        ISO datetime upper bound.
    limit : int
        Maximum results.
    sort : SortOrder
        Sort order.

    Returns
    -------
    list of Entry
        Filtered entries.
    """
    from datetime import datetime

    filters = EntryFilter(
        tags=tag,
        priority=priority,
        since=datetime.fromisoformat(since) if since else None,
        until=datetime.fromisoformat(until) if until else None,
        limit=limit,
        sort=sort,
    )
    try:
        return storage.list_entries(filters)
    except StashError as exc:
        raise _handle_error(exc) from exc


@app.get("/entries/{entry_id}", response_model=Entry)
def get_entry(entry_id: UUID) -> Entry:
    """Get a single entry by UUID.

    Parameters
    ----------
    entry_id : UUID
        Entry identifier.

    Returns
    -------
    Entry
        Full entry record.
    """
    try:
        return storage.get_entry(entry_id)
    except StashError as exc:
        raise _handle_error(exc) from exc


@app.patch("/entries/{entry_id}", response_model=Entry)
def update_entry(entry_id: UUID, body: EntryUpdate) -> Entry:
    """Partially update an entry.

    Parameters
    ----------
    entry_id : UUID
        Entry to update.
    body : EntryUpdate
        Fields to change.

    Returns
    -------
    Entry
        Updated entry.
    """
    try:
        return storage.update_entry(entry_id, body)
    except StashError as exc:
        raise _handle_error(exc) from exc


@app.delete("/entries/{entry_id}", status_code=204, response_class=Response)
def delete_entry(entry_id: UUID) -> Response:
    """Delete an entry by UUID.

    Parameters
    ----------
    entry_id : UUID
        Entry to remove.

    Returns
    -------
    Response
        Empty 204 response on success.
    """
    try:
        storage.remove_entries([entry_id])
    except StashError as exc:
        raise _handle_error(exc) from exc
    return Response(status_code=204)


@app.get("/search", response_model=List[Entry])
def search_entries(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1),
) -> List[Entry]:
    """Search entries by text.

    Parameters
    ----------
    q : str
        Search query.
    limit : int
        Maximum results.

    Returns
    -------
    list of Entry
        Matching entries.
    """
    try:
        return storage.search(SearchQuery(query=q, limit=limit))
    except StashError as exc:
        raise _handle_error(exc) from exc


@app.get("/tags", response_model=List[str])
def list_tags(prefix: Optional[str] = None) -> List[str]:
    """List known tags.

    Parameters
    ----------
    prefix : str, optional
        Filter tags by prefix.

    Returns
    -------
    list of str
        Tag names.
    """
    try:
        return storage.list_tags(prefix=prefix)
    except StashError as exc:
        raise _handle_error(exc) from exc
