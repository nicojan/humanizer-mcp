"""JSON file storage for mcp-humanizer (read-only)."""

import copy
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

VALID_FILES = [
    "foundation",
    "lexical_patterns",
    "structural_patterns",
    "sentiment_tone",
    "discourse_cohesion",
    "psycholinguistic_texture",
    "content_profiles",
    "anti_patterns",
    "caveats",
    "banned_structures",
    "self_review",
]

_CACHE: dict[str, Any] = {}


def _data_dir() -> Path:
    """Resolve the data directory. Defaults to the container path; override
    with HUMANIZER_DATA_DIR for local development and tests."""
    return Path(os.environ.get("HUMANIZER_DATA_DIR", "/app/data"))


def _read_from_disk(filename: str) -> dict[str, Any]:
    filepath = _data_dir() / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filename}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json(filename: str) -> dict[str, Any]:
    """Load a JSON file from the data directory. Cached in-memory after first
    read; container restart (entrypoint git-pull) is the only refresh path.
    Returns a deep copy so callers can safely mutate the result."""
    cached = _CACHE.get(filename)
    if cached is None:
        cached = _read_from_disk(filename)
        _CACHE[filename] = cached
    return copy.deepcopy(cached)


def init_storage() -> None:
    """Initialize the storage layer. Call once at server startup. Pre-warms
    the in-memory cache so the first tool call doesn't pay for 8 disk reads."""
    _data_dir().mkdir(parents=True, exist_ok=True)
    for name in VALID_FILES:
        try:
            _CACHE[name + ".json"] = _read_from_disk(name + ".json")
        except FileNotFoundError:
            logger.warning(f"Data file missing at startup: {name}.json")
    logger.info(f"Storage layer initialized (cached {len(_CACHE)} files)")


def _clear_cache_for_tests() -> None:
    """Test-only: drop the cache so a test can change HUMANIZER_DATA_DIR
    between cases. Production code never calls this."""
    _CACHE.clear()
