"""Group D: rule-of-three DENSITY detector. The rule-of-three is a known AI tell
(AP-011 / AP-020); a single triad is fine, but two or more parallel three-item
coordinations close together is a strong structural signal. This promotes the
'rule-of-three density' check from a manual_review note to a located must_clear
finding (proposed-rules.md #10)."""

from src.checker import run_checks
from src.checker.structures import find_rule_of_three_density


def test_two_adjacent_triads_flagged():
    text = (
        "Every send, payment, or publish goes through a gate. "
        "A person approves, edits, or rejects it."
    )
    res = find_rule_of_three_density(text)
    assert len(res) >= 1
    assert res[0]["type"] == "rule_of_three_density"
    assert res[0]["offset"] >= 0


def test_single_triad_not_flagged():
    assert find_rule_of_three_density(
        "The platform offers data, reporting, and alerts."
    ) == []


def test_distant_triads_not_flagged():
    filler = " ".join(["The team kept working steadily through the quarter."] * 8)
    text = (
        "The platform offers data, reporting, and alerts. "
        + filler
        + " Users can sort, filter, or export their records."
    )
    assert find_rule_of_three_density(text) == []


def test_no_lists_is_clean():
    assert find_rule_of_three_density("We shipped on Tuesday. It worked.") == []


def test_density_surfaces_through_run_checks():
    text = (
        "Every send, payment, or publish goes through a gate. "
        "A person approves, edits, or rejects it."
    )
    r = run_checks(text, "prose")
    assert any(m.get("type") == "rule_of_three_density" for m in r["must_clear"])
