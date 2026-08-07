import pytest

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


# --- markdown structure is not an em-dash digraph (2026-08-06) ---
# AR-002 is a hard gate, so a false positive here blocks a clean check on any
# document containing a markdown table, horizontal rule, or front-matter fence.
@pytest.mark.parametrize(
    "text",
    [
        "| Source | Used for |\n|---|---|\n| Forbes | BS-032 |",
        "| a | b |\n| :--- | ---: |\n| 1 | 2 |",
        "Intro paragraph.\n\n---\n\nNext section.",
        "---\ntitle: notes\n---\n\nBody text.",
        "Heading\n-------\n\nBody text.",
    ],
)
def test_markdown_structure_is_not_flagged(text):
    assert find_emdashes(text) == []


@pytest.mark.parametrize(
    "text",
    [
        "The build failed--again.",
        "He paused -- then answered.",
        "A long run---still an em-dash substitute inside a sentence.",
    ],
)
def test_inline_digraph_still_flagged(text):
    assert find_emdashes(text)
