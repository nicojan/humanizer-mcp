from src.storage.json_store import load_json


def test_enforcement_block_present():
    f = load_json("foundation.json")
    assert "enforcement" in f
    assert "zero_tolerance" in f["enforcement"]
    assert "non_uniformity_scope" in f["enforcement"]


def test_protocol_has_verification_phase():
    f = load_json("foundation.json")
    phases = f["application_protocol"]["phases"]
    assert any("humanizer_check_text" in str(p) for p in phases)


def test_core_principle_scopes_to_tier2():
    f = load_json("foundation.json")
    assert "Tier 2" in f["core_principle"]["explanation"] or "Tier-2" in f["core_principle"]["explanation"]
