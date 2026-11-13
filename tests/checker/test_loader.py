from src.checker.loader import load_hard_phrases, load_regex_structures, load_flagged_terms


def test_hard_phrases_include_didactic_disclaimer():
    phrases = load_hard_phrases()
    assert "it is important to note that" in [p.lower() for p in phrases]


def test_regex_structures_all_have_patterns():
    for s in load_regex_structures():
        assert s["detection"]["method"] == "regex"
        assert s["detection"]["pattern"]


def test_flagged_terms_include_delve_with_alternatives():
    terms = load_flagged_terms()
    delve = next((t for t in terms if t["term"] == "delve"), None)
    assert delve is not None
    assert delve["severity"] == "high"
    assert "examine" in delve["alternatives"] or len(delve["alternatives"]) > 0


def test_flagged_terms_include_transition_phrase():
    terms = load_flagged_terms()
    assert any(t["term"] == "That being said" for t in terms)


def test_flagged_terms_exclude_hard_phrases():
    # "It is important to note that" is promoted to a Tier-1 hard phrase
    # (banned_structures BS-002); it must not also appear as a Tier-2 term,
    # or it would be double-reported in hard_violations and must_clear.
    terms = load_flagged_terms()
    assert not any(
        t["term"].lower() == "it is important to note that" for t in terms
    )


# --- self_review.json: lenient at runtime, strict in CI -----------------------

import logging

import pytest

from src.checker import loader
from src.checker.loader import (
    check_self_review_at_startup,
    load_self_review,
    load_self_review_strict,
)

_GOOD = {
    "id": "good_item",
    "short": "One line.",
    "detail": "The full text.",
    "applies_to": ["all"],
}


def _serve_items(monkeypatch, items):
    real = loader.load_json

    def fake(name):
        if name == "self_review.json":
            return {"self_review": {"items": items}}
        return real(name)

    monkeypatch.setattr(loader, "load_json", fake)


def test_legacy_string_items_are_served_as_all_scoped_objects(monkeypatch):
    _serve_items(monkeypatch, ["Check the stance.", "Read it cold."])
    items = load_self_review()
    assert [i["short"] for i in items] == ["Check the stance.", "Read it cold."]
    assert all(i["detail"] == i["short"] and i["applies_to"] == ["all"] for i in items)
    ids = [i["id"] for i in items]
    assert len(set(ids)) == 2 and all(ids)
    assert ids == [i["id"] for i in load_self_review()]  # stable across calls


def test_malformed_items_are_skipped_with_a_warning_and_the_rest_served(monkeypatch, caplog):
    missing_applies = {k: v for k, v in _GOOD.items() if k != "applies_to"}
    _serve_items(monkeypatch, [missing_applies, 42, _GOOD])
    with caplog.at_level(logging.WARNING, logger="src.checker.loader"):
        items = load_self_review()
    assert [i["id"] for i in items] == ["good_item"]
    assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 2


def test_strict_validator_still_rejects_legacy_and_malformed_items(monkeypatch):
    _serve_items(monkeypatch, ["Check the stance."])
    with pytest.raises(ValueError):
        load_self_review_strict()
    _serve_items(monkeypatch, [{k: v for k, v in _GOOD.items() if k != "applies_to"}])
    with pytest.raises(ValueError):
        load_self_review_strict()


def test_shipped_self_review_data_passes_the_strict_validator():
    assert load_self_review_strict() == load_self_review()


def test_startup_check_logs_the_result_and_never_raises(monkeypatch, caplog):
    _serve_items(monkeypatch, ["old line", {"id": "x"}, _GOOD])
    with caplog.at_level(logging.INFO, logger="src.checker.loader"):
        count = check_self_review_at_startup()
    assert count == 2
    assert any("self_review" in r.getMessage() and "2" in r.getMessage() for r in caplog.records)


def _serve_container(monkeypatch, data):
    real = loader.load_json

    def fake(name):
        return data if name == "self_review.json" else real(name)

    monkeypatch.setattr(loader, "load_json", fake)


@pytest.mark.parametrize(
    "data",
    [
        {"self_review": {"items": None}},
        {"self_review": {"items": "Check the stance."}},
        {"self_review": []},
        [],
    ],
)
def test_startup_check_never_raises_on_a_broken_container(monkeypatch, caplog, data):
    _serve_container(monkeypatch, data)
    with caplog.at_level(logging.ERROR, logger="src.checker.loader"):
        assert check_self_review_at_startup() == 0
    assert any(r.levelno == logging.ERROR and "self_review" in r.getMessage() for r in caplog.records)


def test_a_broken_container_is_an_error_not_a_list_of_characters(monkeypatch):
    _serve_container(monkeypatch, {"self_review": {"items": "Check the stance."}})
    with pytest.raises(ValueError):
        load_self_review()


def test_startup_check_warns_when_legacy_string_items_are_mapped(monkeypatch, caplog):
    _serve_items(monkeypatch, ["old line", "older line", _GOOD])
    with caplog.at_level(logging.WARNING, logger="src.checker.loader"):
        assert check_self_review_at_startup() == 3
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert any("legacy" in m and "2" in m for m in warnings)
