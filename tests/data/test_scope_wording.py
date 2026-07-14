from src.storage.json_store import load_json


def test_uniform_paradox_scoped_to_tier2():
    c = load_json("caveats.json")
    paradox = next(
        x for x in c["core_caveats"] if x["id"] == "uniform_application_paradox"
    )
    assert "Tier 2" in paradox["explanation"] or "Tier-2" in paradox["explanation"]


def test_lexical_application_rule_scoped():
    lex = load_json("lexical_patterns.json")
    assert "Tier 2" in lex["meta"]["application_rule"] or "Tier-2" in lex["meta"]["application_rule"]
