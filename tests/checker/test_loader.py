from src.checker.loader import load_hard_phrases, load_regex_structures, load_flagged_terms


def test_hard_phrases_include_didactic_disclaimer():
    phrases = load_hard_phrases()
    assert "it is important to note that" in [p.lower() for p in phrases]


def test_regex_structures_all_have_patterns():
    for s in load_regex_structures():
        assert s["detection"]["method"] == "regex"
        assert s["detection"]["pattern"]


def test_flagged_terms_include_delve_with_alternatives():
    terms = load_flagged_terms()
    delve = next((t for t in terms if t["term"] == "delve"), None)
    assert delve is not None
    assert delve["severity"] == "high"
    assert "examine" in delve["alternatives"] or len(delve["alternatives"]) > 0


def test_flagged_terms_include_transition_phrase():
    terms = load_flagged_terms()
    assert any(t["term"] == "That being said" for t in terms)


def test_flagged_terms_exclude_hard_phrases():
    # "It is important to note that" is promoted to a Tier-1 hard phrase
    # (banned_structures BS-002); it must not also appear as a Tier-2 term,
    # or it would be double-reported in hard_violations and must_clear.
    terms = load_flagged_terms()
    assert not any(
        t["term"].lower() == "it is important to note that" for t in terms
    )
