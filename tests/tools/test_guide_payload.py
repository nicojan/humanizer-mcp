from src.tools.read import build_guide_payload


def test_guide_payload_phase_zero_is_prohibitions():
    # The hand-written apply_in_order array was removed (duplicated
    # foundation.application_protocol.phases). The equivalent guarantee is
    # now: phase 0 of the application_protocol exists, is the absolute-rules
    # pass, and its stop_condition names every absolute_rules id.
    p = build_guide_payload("prose")
    phases = p["foundation"]["application_protocol"]["phases"]
    phase_zero = phases[0]
    assert phase_zero["phase"] == 0
    assert "absolute" in phase_zero["name"].lower()
    stop = phase_zero["stop_condition"].lower()
    for rule_id in ("ar-001", "ar-002", "ar-003"):
        assert rule_id in stop, f"phase 0 stop_condition missing {rule_id}"


def test_guide_payload_has_verification_block():
    p = build_guide_payload("prose")
    assert p["verification"]["tool"] == "humanizer_check_text"
    assert "prohibitions_clear" in p["verification"]["instruction"]


def test_guide_payload_keeps_existing_dimensions():
    # The "additive" claim for humanizer_get_guide is the key consumer-safety
    # property: existing cross-server consumers must continue to find every
    # dimension key they used to find. Assert ALL of them.
    p = build_guide_payload("prose")
    for key in (
        "foundation",
        "lexical_patterns",
        "structural_patterns",
        "sentiment_tone",
        "discourse_cohesion",
        "psycholinguistic_texture",
        "anti_patterns",
        "caveats",
        "content_profile",
    ):
        assert key in p, f"missing dimension: {key}"
