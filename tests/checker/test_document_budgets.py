"""Document budgets: the instrument the protocol requirement never had.

caveats.per_section_checks_miss_document_budgets (2026-08-10) recorded the gap:
several rules budget a shape at one instance per piece, the rubric says to count
across the assembled document, and check_text is stateless, so nothing counted.
Found on a 39-page case study where the appended-significance label had been
justified four separate times, once per section.

Counted here: BS-011, BS-018, BS-038, BS-039, the four budgeted shapes that a
detector can actually find. The judgment-bound ones (the appositive label, the
aphorism, the anaphoric run) stay in the self_review rubric, because a detector
that cannot find one instance cannot count three.
"""

import json
import pathlib

from src.checker import run_checks
from src.checker.budgets import find_budget_overruns
from src.checker.loader import load_document_budgets

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

THREE_ANTITHESES = (
    "The work is judgement, not process. Teams ship early and often. "
    "The answer is restraint, not addition. Reviews stay short. "
    "Design is clarity, not decoration."
)
ONE_ANTITHESIS = "The work is judgement, not process. Teams ship early and often."


def _budgets(text: str) -> list[dict]:
    return [
        m for m in run_checks(text, "prose")["must_clear"]
        if m.get("type") == "document_budget"
    ]


def test_one_instance_is_ordinary_writing():
    assert _budgets(ONE_ANTITHESIS) == []


def test_three_instances_are_a_budget_finding():
    found = _budgets(THREE_ANTITHESES)
    assert len(found) == 1
    finding = found[0]
    assert finding["id"] == "BS-011"
    assert finding["count"] == 3
    assert finding["budget"] == 1
    # The honest wording matters: the checker still only sees what it is handed.
    assert "text supplied" in finding["detail"]
    assert "assembled document" in finding["fix"]


def test_the_underlying_findings_are_still_reported_individually():
    """The budget finding is additional, never a replacement: a writer still
    needs the offsets to fix the instances."""
    must = run_checks(THREE_ANTITHESES, "prose")["must_clear"]
    individual = [m for m in must if m.get("type") == "banned_structure"]
    assert len([m for m in individual if m["id"] == "BS-011"]) == 3


def test_budgets_are_data_driven_and_cover_the_mechanized_shapes():
    """Four shapes at 2026-09-18; BS-053 and the budget-only BS-055 joined on
    2026-09-29 (tests/checker/test_worksheet_tells_2026_09.py)."""
    budgets, names = load_document_budgets()
    assert budgets == {
        "BS-011": 1, "BS-018": 1, "BS-038": 1, "BS-039": 1, "BS-053": 1, "BS-055": 1,
    }
    assert names["BS-011"] == "x_not_y_contrastive"
    entries = json.loads((DATA / "banned_structures.json").read_text())["structures"]
    budgeted = {s["id"] for s in entries if s.get("document_budget")}
    assert budgeted == set(budgets)


def test_unbudgeted_rules_are_never_counted():
    """Control in the same run: a rule with no document_budget can repeat freely."""
    findings = [{"id": "BS-006"}] * 5 + [{"id": "BS-011"}]
    assert find_budget_overruns(findings, {"BS-011": 1}, {}) == []


def test_the_counter_reads_ids_not_positions():
    findings = [{"id": "BS-011"}, {"id": "BS-011"}, {"type": "burstiness"}]
    out = find_budget_overruns(findings, {"BS-011": 1}, {"BS-011": "x_not_y_contrastive"})
    assert len(out) == 1 and out[0]["count"] == 2


def test_caveat_records_that_the_mechanical_half_now_exists():
    caveats = json.loads((DATA / "caveats.json").read_text())["core_caveats"]
    entry = {c["id"]: c for c in caveats}["per_section_checks_miss_document_budgets"]
    assert "document_budget" in entry["explanation"]
    assert "2026-09-18" in entry["explanation"]
