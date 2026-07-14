from src.checker.structures import find_regex_structures, find_heuristic_structures

NEG_PARALLEL = {
    "id": "BS-006",
    "name": "negative_parallelism",
    "fix": "State the point directly.",
    "detection": {
        "method": "regex",
        "pattern": r"\bnot (just|only)\b[^.?!]{0,60}?\bbut\b",
        "confidence": "medium",
    },
}


def test_regex_match_negative_parallelism():
    res = find_regex_structures(
        "This is not just efficient, but also scalable.", [NEG_PARALLEL]
    )
    assert len(res) == 1
    assert res[0]["id"] == "BS-006"
    assert res[0]["type"] == "banned_structure"
    assert res[0]["confidence"] == "medium"


def test_regex_no_match_clean():
    res = find_regex_structures("The approach is efficient and scalable.", [NEG_PARALLEL])
    assert res == []


def test_regex_skips_non_regex_entries():
    heuristic_entry = {"id": "BS-012", "name": "x", "fix": "y", "detection": {"method": "heuristic"}}
    assert find_regex_structures("anything", [heuristic_entry]) == []


def test_heuristic_stacked_nominalization():
    text = (
        "The implementation of the optimization of resource allocation led to "
        "the enhancement of efficiency."
    )
    res = find_heuristic_structures(text)
    assert any(r["name"] == "stacked_nominalization" for r in res)


def test_heuristic_this_chain():
    text = "This framework helps a lot. This detection works well. This result matters here."
    res = find_heuristic_structures(text)
    assert any(r["name"] == "this_chain" for r in res)


def test_heuristic_no_false_positive():
    text = "We shipped on Tuesday. The team was tired. Everyone went home early."
    res = find_heuristic_structures(text)
    assert res == []
