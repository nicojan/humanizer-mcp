"""PR2 data invariants: new banned_structures (BS-017..BS-020), anti-patterns
(AP-032 lexical, AP-033 structural), the credibility_insistence lexical block,
and the abstraction-as-agent manual_review line."""

from src.checker import run_checks
from src.storage.json_store import load_json


def test_new_banned_structures_present_and_valid():
    structures = {s["id"]: s for s in load_json("banned_structures.json")["structures"]}
    for sid in ("BS-017", "BS-018", "BS-019", "BS-020"):
        assert sid in structures, f"missing {sid}"
        s = structures[sid]
        assert s["name"] and s["fix"]
        assert s["gate"] == "checklist"
        assert s["detection"]["method"] in ("regex", "heuristic")
        if s["detection"]["method"] == "regex":
            assert s["detection"]["pattern"]


def test_new_antipatterns_present_emdash_free():
    pats = {p["id"]: p for p in load_json("anti_patterns.json")["patterns"]}
    for pid in ("AP-032", "AP-033"):
        assert pid in pats, f"missing {pid}"
        assert "—" not in pats[pid]["after"], f"{pid} after has an em-dash"
        assert pats[pid]["before"] and pats[pid]["explanation"]
    assert pats["AP-032"]["category"] == "lexical"


def test_credibility_insistence_block_in_lexical():
    lex = load_json("lexical_patterns.json")
    block = lex.get("credibility_insistence")
    assert block, "credibility_insistence block missing"
    assert isinstance(block.get("tokens"), list) and "real" in block["tokens"]
    # threshold params present so the detector and data agree
    assert "same_token_min" in block and "rate_per_words" in block


def test_abstraction_as_agent_manual_review_line():
    r = run_checks("The team shipped the update on a quiet Tuesday afternoon.", "prose")
    joined = " ".join(r["manual_review"]).lower()
    assert "abstraction-as-agent" in joined or "abstract noun" in joined
