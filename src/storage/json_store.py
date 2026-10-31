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

_CONTAINER_DATA_DIR = Path("/app/data")
_REPO_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _data_dir() -> Path:
    """Resolve the data directory. HUMANIZER_DATA_DIR wins when set; otherwise
    the container path, or the repo's data/ when run outside the container."""
    override = os.environ.get("HUMANIZER_DATA_DIR")
    if override:
        return Path(override)
    if _CONTAINER_DATA_DIR.is_dir():
        return _CONTAINER_DATA_DIR
    return _REPO_DATA_DIR


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
