"""Token-efficiency trims: the foundation payload must not double-ship the
application_protocol (it has its own tool and its own 'minimum viable'
contract), pure-exposition `theory` blocks must be stripped like
`research_basis`, and the load-bearing content_profiles `notes` must survive."""

from src.storage.json_store import load_json
from src.tools.read import (
    _strip_meta,
    build_foundation_payload,
    build_guide_payload,
)


def test_foundation_payload_excludes_application_protocol():
    p = build_foundation_payload()
    assert "application_protocol" not in p
    # …but the non-negotiables and the phase-order signal remain.
    assert "absolute_rules" in p
    assert "enforcement" in p
    assert "priority_hierarchy" in p


def test_application_protocol_still_available_raw():
    # The dedicated humanizer_get_application_protocol tool reads it straight
    # from the data file; removing it from the foundation payload must not
    # touch the source.
    assert "application_protocol" in load_json("foundation.json")


def test_guide_still_includes_application_protocol():
    # Consumer-safety contract (test_guide_payload.py): cross-server consumers
    # of the full guide still find the phase plan.
    p = build_guide_payload("prose")
    assert "application_protocol" in p["foundation"]


def test_theory_blocks_stripped_from_psycholinguistic():
    served = _strip_meta(load_json("psycholinguistic_texture.json"))
    for key, sub in served.items():
        if isinstance(sub, dict):
            assert "theory" not in sub, f"theory survived in {key}"


def test_theory_stripped_in_full_guide():
    p = build_guide_payload("prose")
    for key, sub in p["psycholinguistic_texture"].items():
        if isinstance(sub, dict):
            assert "theory" not in sub


def test_content_profile_notes_preserved():
    # `notes` is the actionable payload of content_profiles — it must NOT be
    # caught by the theory/research_basis stripping.
    profiles = load_json("content_profiles.json")["profiles"]
    served = _strip_meta(load_json("content_profiles.json"))
    # marketing lexical note is the canonical high-value one.
    raw_note = profiles["marketing"]["layer_adjustments"]["lexical_patterns"]["notes"]
    assert raw_note  # exists in source
    # build_guide_payload routes profiles through _drop_keys; confirm notes live.
    p = build_guide_payload("marketing")
    assert "notes" in p["content_profile"]["layer_adjustments"]["lexical_patterns"]
