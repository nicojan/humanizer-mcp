import re

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


def test_flag_in_prose_is_not_an_emdash():
    assert find_emdashes("Run pip install --upgrade pip before you start.") == []


def test_flag_in_backticks_is_not_an_emdash():
    assert find_emdashes("Run `npm install --save-dev jest` first.") == []


def test_fenced_code_block_is_skipped():
    assert find_emdashes("Setup:\n```\nnpm install --save-dev jest\n```\nDone.") == []


def test_typed_emdash_digraph_still_flagged_both_spacings():
    assert len(find_emdashes("The plan--if it works--saves a week.")) == 2
    assert len(find_emdashes("The plan -- if it works -- saves a week.")) == 2


def test_emdash_beside_a_code_span_still_fires():
    assert len(find_emdashes("Use `git push --force` sparingly—it rewrites history.")) == 1


def test_crlf_fence_skipped_and_crlf_prose_flagged():
    t = "Intro.\r\n```\r\nnpm ci --quiet\r\n```\r\nThe plan--if it works--ships."
    assert len(find_emdashes(t)) == 2


def test_unclosed_backtick_does_not_hide_prose():
    assert len(find_emdashes("A stray ` tick, and then the plan--if it works.")) == 1


def test_emdash_fix_text_has_no_emdash_and_no_colon():
    fix = find_emdashes("A—B")[0]["fix"]
    assert "—" not in fix and "--" not in fix
    # "semicolon" legitimately contains "colon"; ban the standalone word only.
    assert not re.search(r"\bcolon\b", fix.lower())


def test_dash_glued_to_a_quote_still_fires():
    assert len(find_emdashes('He said "--and when I came home.')) == 1
    assert len(find_emdashes("It ended,'--but then it began.")) == 1
    assert len(find_emdashes("He said “--and when I came home.")) == 1
    assert len(find_emdashes("It ended,‘--but then it began.")) == 1


def test_quoted_flag_is_not_an_emdash():
    assert find_emdashes('Pass "--verbose" to see more.') == []
    assert find_emdashes("Pass '--save-dev' to see more.") == []
    assert find_emdashes("Pass “--verbose” to see more.") == []
    assert find_emdashes("Pass ‘--save-dev’ to see more.") == []


def test_unclosed_fence_hides_nothing():
    assert len(find_emdashes("Setup:\n```\nnpm ci\nThe plan--if it works--ships.")) == 2


def test_closer_without_a_recognised_opener_hides_nothing():
    t = "- ```bash\n  npm ci\n  ```\nThe plan--if it works--ships."
    assert len(find_emdashes(t)) == 2


def test_backtick_in_info_string_is_not_a_fence():
    t = "```npm ci``` is slow--and noisy.\nThe plan--if it works--ships."
    assert len(find_emdashes(t)) == 3


def test_non_flag_digraph_inside_backtick_fence_is_skipped():
    assert find_emdashes("```\nx = a--b\n```") == []
    assert find_emdashes("Go:\n```python\nx = a--b\ny = c--d\n```\nDone.") == []
    assert find_emdashes("```\n--Dana and i--\n```") == []


def test_non_flag_digraph_inside_tilde_fence_is_skipped():
    assert find_emdashes("~~~\ny = a--b\n~~~") == []


def test_fence_closer_must_be_at_least_as_long_and_same_char():
    assert find_emdashes("````\na--b\n```\nc--d\n````") == []
    # a tilde line does not close a backtick fence, so the fence is unclosed
    assert len(find_emdashes("```\na--b\n~~~\n")) == 1


def test_fence_indent_zero_to_three_spaces():
    assert find_emdashes("   ```\na--b\n   ```") == []
    assert len(find_emdashes("    ```\na--b\n    ```")) == 1


def test_non_flag_digraph_inside_inline_span_is_skipped():
    assert find_emdashes("Use `i--` here.") == []
    assert find_emdashes("Use `.btn--Primary` here.") == []


# U+2014 fires inside code: a draft handed over in a fence is the deliverable.
@pytest.mark.parametrize(
    "text",
    [
        "```\nA\u2014B\n```",
        "~~~\nA\u2014B\n~~~",
        "Use `a\u2014b` here.",
        "```markdown\nThe plan\u2014if it works\u2014ships Friday.\n```",
        "Go:\n```python\nx = a--b\ny = a \u2014 b\n```\nDone.",
    ],
)
def test_emdash_character_fires_inside_code(text):
    assert find_emdashes(text)


def test_fenced_draft_counts_each_emdash_character():
    t = "```markdown\nThe plan\u2014if it works\u2014ships Friday.\n```"
    assert len(find_emdashes(t)) == 2


# Attribution, sign-off and capitalised dialogue dashes are typed em-dashes;
# only a lowercase flag shape is skipped outside code.
@pytest.mark.parametrize(
    "text",
    [
        "> --Oscar Wilde",
        "Thanks for reading.\n\n--Dana",
        "--No, I said.",
        'He wrote "--Dana" at the end.',
    ],
)
def test_capitalised_dash_lead_fires(text):
    assert len(find_emdashes(text)) == 1


@pytest.mark.parametrize(
    "text",
    [
        "Use git push --force sparingly.",
        "Add the flag (--verbose) to see more.",
        'Pass "--verbose" to see more.',
        "--verbose is the flag to pass.",
        "Run it\n--dry-run first.",
    ],
)
def test_lowercase_flag_shapes_are_still_skipped(text):
    assert find_emdashes(text) == []


def test_multi_backtick_inline_span():
    assert find_emdashes("Use ``a`b--c`` here.") == []
    assert len(find_emdashes("Use ``a`b`` then c--d.")) == 1


@pytest.mark.parametrize("opener", ["```a\n", "~~~a\n"])
def test_unclosed_opener_run_at_the_cap_is_fast(opener):
    import time

    text = opener * 20_000  # 100,000 characters, every line an unclosed opener
    start = time.perf_counter()
    assert find_emdashes(text) == []
    assert time.perf_counter() - start < 0.5


def test_unclosed_opener_run_still_flags_prose_after_it():
    assert len(find_emdashes("```a\n```ab\nThe plan--if it works.")) == 1


def test_shorter_opener_after_a_failed_longer_one_still_finds_its_closer():
    # the 4-backtick opener has no 4+ closer and fails; the 3-backtick opener
    # that follows must still close on the 3-backtick line and hide x--y
    assert len(find_emdashes("````a\n```b\nx--y\n```\nz--w\n")) == 1


@pytest.mark.parametrize("char", ["`", "~"])
def test_descending_length_unclosed_openers_at_the_cap_are_fast(char):
    import time

    # 258..3 long fence lines (about 33k chars) then empty lines up to the cap
    head = "".join(char * n + "\n" for n in range(258, 2, -1))
    text = head + "\n" * (100_000 - len(head))
    start = time.perf_counter()
    assert find_emdashes(text) == []
    assert time.perf_counter() - start < 0.5


def test_closer_indented_four_spaces_does_not_close():
    t = "```\na--b\n        ```\nc--d\n```\n"
    assert find_emdashes(t) == []
    # with no real closer the fence is unclosed, so both dashes are visible
    assert len(find_emdashes("```\na--b\n    ```\nc--d\n")) == 2


@pytest.mark.parametrize("unit", ["—", "\n--Dana", "```\n—\n```\n", "`—` "])
def test_new_triggers_repeated_to_the_cap_are_fast(unit):
    import time

    text = unit * (100_000 // len(unit))
    start = time.perf_counter()
    assert find_emdashes(text)
    assert time.perf_counter() - start < 1.0
