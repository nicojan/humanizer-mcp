"""humanizer_get_guide paging (2026-09-29).

The full guide measured 166,067 characters for content_type="prose" after
this round's additions, over 40k tokens, over the 25k-token tool-output cap in Claude Code; a drafting
session had to parse it from a dump file. `part` splits it into four pages that
each fit, while the default stays the full payload so existing consumers keep
every dimension key (tests/tools/test_guide_payload.py).
"""

import json

import pytest

from src.tools.read import GUIDE_PARTS, build_guide_part, build_guide_payload

# Under a 25k-token cap even at a dense 3 characters a token.
MAX_PART_CHARS = 75_000


def _size(obj) -> int:
    return len(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))


@pytest.mark.parametrize("content_type", ["prose", "marketing", "academic", "technical", "not-a-type"])
@pytest.mark.parametrize("part", list(GUIDE_PARTS))
def test_each_part_fits_a_client_output_cap(part, content_type):
    """An unknown content_type returns every profile with a warning, which
    lands in 'core', so it is measured too."""
    assert _size(build_guide_part(content_type, part)) < MAX_PART_CHARS, (part, content_type)


def test_the_parts_together_cover_the_full_guide():
    full = build_guide_payload("prose")
    seen: dict = {}
    for part in GUIDE_PARTS:
        payload = build_guide_part("prose", part)
        for key, value in payload.items():
            if key.startswith("guide_"):
                continue
            assert key not in seen or key == "verification", f"{key} is in two parts"
            seen[key] = value
    assert set(seen) == set(full)
    for key in full:
        assert seen[key] == full[key], key


def test_core_names_what_to_fetch_next():
    core = build_guide_part("prose", "core")
    assert core["guide_part"] == "core"
    assert core["guide_parts_remaining"] == ["lexical", "anti_patterns", "caveats"]
    assert "foundation" in core and "verification" in core


def test_all_is_the_legacy_full_payload():
    assert build_guide_part("prose", "all") == build_guide_payload("prose")


def test_unknown_part_is_rejected():
    with pytest.raises(ValueError):
        build_guide_part("prose", "everything")
