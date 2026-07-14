from src.checker.inflect import inflections


def test_inflections_delve():
    f = inflections("delve")
    assert {"delve", "delves", "delved", "delving"} <= f


def test_inflections_rely():
    f = inflections("rely")
    assert "relies" in f and "relied" in f


def test_multiword_returns_itself_only():
    assert inflections("a key takeaway is") == {"a key takeaway is"}
