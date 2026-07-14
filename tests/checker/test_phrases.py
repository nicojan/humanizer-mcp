from src.checker.phrases import find_phrases, find_flagged_terms


def test_find_phrases_boundary_match():
    hits = find_phrases(
        "It is important to note that we shipped.",
        ["it is important to note that"],
    )
    assert len(hits) == 1
    assert hits[0][0] == "it is important to note that"
    assert hits[0][1] == 0


def test_find_phrases_absent():
    assert find_phrases("Plain prose here.", ["without further ado"]) == []


def test_find_flagged_terms_inflected():
    res = find_flagged_terms(
        "We are delving into the results.",
        [{"term": "delve", "severity": "high", "alternatives": ["dig into"]}],
    )
    assert len(res) == 1
    assert res[0]["term"] == "delve"
    assert res[0]["count"] == 1
    assert res[0]["severity"] == "high"


def test_find_flagged_terms_absent():
    res = find_flagged_terms(
        "Plain text.",
        [{"term": "delve", "severity": "high", "alternatives": []}],
    )
    assert res == []


def test_find_flagged_terms_multiword():
    res = find_flagged_terms(
        "That being said, we moved on.",
        [{"term": "That being said", "severity": "high", "alternatives": ["However"]}],
    )
    assert res and res[0]["count"] == 1
