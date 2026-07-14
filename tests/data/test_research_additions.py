"""Groups C + F: anti-pattern rewrite templates for the new discourse tells, and
research-backed caveats. Data invariants only — behavior is covered in
tests/checker/test_research_lexical_structures.py."""

from src.storage.json_store import load_json


def test_new_antipatterns_present():
    pats = load_json("anti_patterns.json")["patterns"]
    ids = {p["id"] for p in pats}
    for new_id in ("AP-029", "AP-030", "AP-031"):
        assert new_id in ids, f"missing anti-pattern {new_id}"


def test_every_antipattern_after_is_emdash_free():
    # AR-002: every 'after' (the humanized exemplar) must contain no em-dash.
    for p in load_json("anti_patterns.json")["patterns"]:
        assert "—" not in p["after"], f"{p['id']} after contains an em-dash"


def test_new_antipatterns_have_full_schema():
    new = {
        p["id"]: p
        for p in load_json("anti_patterns.json")["patterns"]
        if p["id"] in ("AP-029", "AP-030", "AP-031")
    }
    for p in new.values():
        assert p["category"] in (
            "lexical",
            "structural",
            "sentiment",
            "discourse",
            "psycholinguistic",
        )
        assert p["before"] and p["after"] and p["explanation"]


def test_research_caveats_present():
    ids = {c["id"] for c in load_json("caveats.json")["core_caveats"]}
    for cid in (
        "em_dash_model_specific",
        "flow_over_surface_features",
        "sentence_length_mean_not_a_signal",
    ):
        assert cid in ids, f"missing caveat {cid}"


def test_every_caveat_has_statement_and_explanation():
    for c in load_json("caveats.json")["core_caveats"]:
        assert c["id"] and c["statement"] and c["explanation"]


def test_guidance_sub_objects_present():
    assert "cross_segment_variation" in load_json("structural_patterns.json")
    assert "explicit_antithesis_and_reused_shape" in load_json(
        "discourse_cohesion.json"
    )


def test_application_protocol_covers_new_sub_objects():
    # foundation.application_protocol.coverage_invariant: new sub-objects in an
    # existing layer must be registered as rule_paths so the full traversal
    # still surveys the complete rule set.
    paths = []
    for phase in load_json("foundation.json")["application_protocol"]["phases"]:
        paths.extend(phase.get("rule_paths", []))
    assert "structural_patterns.cross_segment_variation" in paths
    assert "discourse_cohesion.explicit_antithesis_and_reused_shape" in paths

