"""The self-review rubric arrives short by default and full once.

Every humanizer_check_text report carries the rubric, so the default is one
short line per item, filtered by content_type. The model asks for the full
detail texts once, on its final check (rubric="full"). `history` holds the
maintainer notes (measurements, dates, rule ids) and is never served.
"""

import re

import pytest

from src.checker import run_checks
from src.checker.loader import load_self_review, load_self_review_strict
from src.checker.report import _MANUAL_REVIEW, _NEXT_ACTION, assemble_report
from src.checker.rubric import rubric_lines
from src.content_types import CONTENT_TYPE_ALIASES, canonical_content_type
from src.tools.check import check_text_handler
from tests.data.test_guide_consistency import _QUOTE_PATTERNS, fires

EM_DASH = "—"
_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")
_PORTFOLIO = ["case_study", "resume", "marketing", "label"]


def item(item_id):
    return next(i for i in load_self_review() if i["id"] == item_id)


def _served_fields() -> list[tuple[str, str, str]]:
    return [
        (it["id"], field, it[field])
        for it in load_self_review()
        for field in ("short", "detail")
    ]


# ---------------------------------------------------------------------------
# Brief tests
# ---------------------------------------------------------------------------


def test_rubric_items_are_objects_with_the_four_fields():
    for it in load_self_review():
        assert {"id", "short", "detail", "applies_to"} <= set(it)


def test_short_lines_are_actionable_on_their_own():
    for line in rubric_lines(None, "short"):
        assert len(line) <= 200 and line.rstrip()[-1] in ".?", line


def test_default_report_carries_short_lines_for_its_content_type():
    r = run_checks("We shipped on Tuesday. The team was tired but glad.", "technical")
    assert r["manual_review"] == rubric_lines("technical", "short")
    assert item("cold_reader_test")["short"] not in r["manual_review"]


def test_full_rubric_returns_detail_texts():
    full = run_checks("We shipped on Tuesday.", "case_study", rubric="full")["manual_review"]
    assert full == rubric_lines("case_study", "full") and item("cold_reader_test")["detail"] in full


def test_unknown_content_types_keep_every_all_item():
    all_items = [i["short"] for i in load_self_review() if "all" in i["applies_to"]]
    for ct in (None, "newsletter", "label"):
        lines = rubric_lines(ct, "short")
        assert lines and set(all_items) <= set(lines)


def test_history_is_never_served():
    shown = " ".join(rubric_lines(None, "full"))
    for it in load_self_review():
        if it.get("history"):
            assert it["history"] not in shown


def test_next_action_names_the_final_full_call_and_the_two_round_limit():
    na = run_checks("Anything.")["next_action"]
    assert 'rubric="full"' in na and "flagged span" in na and "two fix rounds" in na


def test_default_report_is_small():
    out = check_text_handler("We shipped on Tuesday. The team was tired but glad.", "prose")
    assert len(out) < 6000


# ---------------------------------------------------------------------------
# Shape and filtering
# ---------------------------------------------------------------------------


def test_items_have_unique_snake_case_ids_and_known_types():
    items = load_self_review_strict()
    assert len(items) == 19
    ids = [i["id"] for i in items]
    assert len(set(ids)) == len(ids)
    known = set(CONTENT_TYPE_ALIASES.values()) | {"all"}
    for it in items:
        assert _SNAKE.match(it["id"]), it["id"]
        assert it["applies_to"] and set(it["applies_to"]) <= known, it["id"]
        assert set(it) <= {"id", "short", "detail", "applies_to", "history"}, it["id"]
        assert all(isinstance(it[k], str) and it[k].strip() for k in ("short", "detail"))


def test_portfolio_and_reader_contact_items_are_scoped():
    for item_id in ("so_tail", "backstory_and_self_portrait", "cold_reader_test"):
        assert item(item_id)["applies_to"] == _PORTFOLIO, item_id
    assert item("reader_contact")["applies_to"] == ["general_prose", "marketing", "case_study"]


def test_label_copy_keeps_the_portfolio_items_and_drops_the_prose_texture_items():
    lines = rubric_lines("label", "short")
    for item_id in ("so_tail", "backstory_and_self_portrait", "cold_reader_test"):
        assert item(item_id)["short"] in lines, item_id
    for item_id in ("reader_contact", "rhythm", "section_variation"):
        assert "label" not in item(item_id)["applies_to"], item_id
        assert item(item_id)["short"] not in lines, item_id


def test_missing_and_unknown_types_get_every_item():
    every = [i["short"] for i in load_self_review()]
    assert rubric_lines(None) == every
    assert rubric_lines("newsletter") == every


def test_aliases_resolve_before_filtering():
    assert rubric_lines("portfolio") == rubric_lines("case_study")
    assert rubric_lines("prose") == rubric_lines("general_prose")
    assert item("cold_reader_test")["short"] not in rubric_lines("prose")
    assert item("cold_reader_test")["short"] in rubric_lines("cv")


def test_rubric_lines_rejects_an_unknown_mode():
    with pytest.raises(ValueError):
        rubric_lines(None, "long")


def test_canonical_content_type():
    assert canonical_content_type(None) is None
    assert canonical_content_type("Tech") == "technical"
    assert canonical_content_type(" portfolio ") == "case_study"
    for ct in ("label", "labels", "notes"):
        assert canonical_content_type(ct) == "label"
    assert canonical_content_type("creative") == "creative"
    assert canonical_content_type("newsletter") is None


def test_report_fallback_is_three_generic_lines():
    assert len(_MANUAL_REVIEW) == 3
    joined = " ".join(_MANUAL_REVIEW)
    assert "stance" in joined and "cold reader" in joined and 'rubric="full"' in joined
    assert assemble_report([], [], {})["manual_review"] == _MANUAL_REVIEW


def test_next_action_is_verbatim():
    assert _NEXT_ACTION == (
        "Resolve every hard_violation. For each must_clear item, rewrite only the "
        "flagged span and keep the rest of the draft as it is, or justify the item. "
        "Re-run humanizer_check_text; stop after two fix rounds and justify any "
        "must_clear item left. A hard_violation is never justified, so keep fixing "
        "until prohibitions_clear is true. Then run one last check on the assembled "
        "document with rubric=\"full\" "
        "and do the self-review against your draft, changing only the spans an item "
        "points to. If the self-review changed anything, run humanizer_check_text "
        "once more and confirm prohibitions_clear is true before returning."
    )


# ---------------------------------------------------------------------------
# Served rubric text carries none of the tells it warns against
# ---------------------------------------------------------------------------


def outside_quotes(text: str) -> str:
    """The text with every quoted example replaced by a neutral word, so the
    rubric's own prose is checked apart from the bad forms it quotes (those are
    covered by the quote test in test_guide_consistency)."""
    for pattern in _QUOTE_PATTERNS:
        text = pattern.sub("example", text)
    return text


_TELLS = {
    "intensifier": re.compile(r"\b(?:genuine(?:ly)?|honestly|actually|real|really|quietly)\b", re.I),
    "load-bearing": re.compile(r"load-bearing", re.I),
    "x_not_y": re.compile(r",\s+not\b|\bnot just\b", re.I),
    "colon": re.compile(r":"),
    "question": re.compile(r"\?"),
    "bold": re.compile(r"\*\*"),
    "em_dash": re.compile(EM_DASH),
}
_AND_CHAIN = re.compile(r"(?:,\s+and\b[^.]*){2,}")


def test_tell_scan_control():
    assert outside_quotes("Cut 'the real job' and say it.") == "Cut example and say it."
    bad = "This is really it: the load-bearing work, not the words — **bold**?"
    hits = {name for name, rx in _TELLS.items() if rx.search(outside_quotes(bad))}
    assert hits == set(_TELLS)
    assert _AND_CHAIN.search("We cut it, and we kept it, and we left.")
    assert not _AND_CHAIN.search("We cut it, and we left. Then we kept it, and slept.")


def test_rubric_prose_carries_no_tells():
    offenders = []
    for item_id, field, text in _served_fields():
        prose = outside_quotes(text)
        for name, rx in _TELLS.items():
            if rx.search(prose):
                offenders.append((item_id, field, name))
        if _AND_CHAIN.search(prose):
            offenders.append((item_id, field, "and_chain"))
    assert offenders == []


def test_no_em_dash_in_any_short_or_detail():
    assert [(i, f) for i, f, t in _served_fields() if EM_DASH in t] == []


def test_rubric_prose_passes_the_checker():
    firing = [(i, f, fires(outside_quotes(t))) for i, f, t in _served_fields()]
    assert [x for x in firing if x[2]] == []


def test_rubric_prose_checker_control():
    # A tell outside quotes fires; the same tell inside quotes is replaced.
    assert fires(outside_quotes("This is a pivotal moment."))
    assert not fires(outside_quotes("Cut 'a pivotal moment' from the draft."))


def test_shorts_are_single_lines():
    for it in load_self_review():
        assert "\n" not in it["short"], it["id"]


def test_details_carry_no_maintainer_history():
    history = re.compile(
        r"\b20\d\d\b|\d+/\d+ precision|\bA reviewer\b|\b(?:BS|AP)-\d{3}\b|rebuild|tests?/|\.py\b"
    )
    assert [(i, f) for i, f, t in _served_fields() if history.search(outside_quotes(t))] == []
    assert history.search(outside_quotes("Measured in 2026 as BS-013."))


def test_anaphora_item_drops_bold_and_genuine():
    detail = item("anaphora")["detail"]
    assert "**" not in detail and "genuine" not in detail.lower()


def test_contrast_item_names_the_single_flip_as_a_whole_piece_judgment():
    detail = item("contrastive_x_not_y")["detail"]
    assert "It's not X. It's Y." in detail
    assert "whole piece" in detail and "two or more" in detail
    assert "contracted or not" not in detail
    assert "It is not a tool. It is a partner." in detail and "on its own" in detail
