from src.checker.emdash import find_emdashes


def test_emdash_unicode_detected():
    v = find_emdashes("The plan — which was bold — failed.")
    assert len(v) == 2
    assert all(x["type"] == "em_dash" and x["rule"] == "AR-002" for x in v)


def test_double_hyphen_detected():
    v = find_emdashes("Wait--what happened?")
    assert len(v) == 1


def test_clean_text_no_emdash():
    assert find_emdashes("A clean sentence, with a comma.") == []


def test_endash_not_flagged():
    assert find_emdashes("Pages 10–20 are key.") == []
