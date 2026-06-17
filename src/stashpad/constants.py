"""Shared constants for Stash."""

from __future__ import annotations

import re

# Vault storage
VAULT_FILENAME = "vault.json"
DEFAULT_VAULT_NAME = "default"
VAULT_SCHEMA_VERSION = "1"

# CLI defaults
DEFAULT_SEARCH_LIMIT = 20
DEFAULT_LIST_LIMIT = 50
DEFAULT_PINS_LIMIT = 10
DEFAULT_PICK_LIMIT = 100
STDIN_CONTENT_ALIAS = "-"

# Search ranking: field weights (title highest, then tags, content, URL)
TITLE_MATCH_WEIGHT = 100.0
TAG_MATCH_WEIGHT = 60.0
CONTENT_MATCH_WEIGHT = 40.0
URL_MATCH_WEIGHT = 30.0

# Search ranking: non-text boosts
PRIORITY_BOOST_HIGH = 15.0
PRIORITY_BOOST_MEDIUM = 8.0
PRIORITY_BOOST_LOW = 0.0
RECENCY_BOOST_CAP = 10.0
OPENED_BOOST_CAP = 20.0
BOOST_HALF_LIFE_DAYS = 14.0

# Duplicate detection
DUPLICATE_SIMILARITY_THRESHOLD = 0.85

# Search ranking: fuzzy matching
FUZZY_MATCH_DISCOUNT = 0.85
WORD_TIGHTNESS_BASE = 0.7
WORD_TIGHTNESS_RANGE = 0.3
WORD_PATTERN = re.compile(r"\w+")
