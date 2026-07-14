from src.checker.util import excerpt


def test_excerpt_trims_and_ellipsizes():
    text = "a" * 100 + "TARGET" + "b" * 100
    out = excerpt(text, 100, 106, radius=10)
    assert "TARGET" in out
    assert out.startswith("…") and out.endswith("…")


def test_excerpt_no_ellipsis_at_bounds():
    out = excerpt("short text", 0, 5, radius=40)
    assert not out.startswith("…") and not out.endswith("…")
