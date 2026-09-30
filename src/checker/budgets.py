"""Document-level budgets for shapes that are ordinary once and a tic three times.

caveats.per_section_checks_miss_document_budgets recorded the gap this closes:
several rules budget a shape at one instance per piece, the rubric says to count
them across the assembled document, and check_text is stateless and per-call, so
nothing counted. A writer working section by section could justify the same
shape four times and never see the pattern.

What this does NOT fix, and the wording of every finding says so: the checker
still only sees the text it is handed. A section-by-section walk still under-
counts. The protocol requirement (run the last check on the assembled document)
stands, and this makes it pay off instead of being advice with no instrument.

Only the mechanized shapes are counted. The budgeted items that need judgment
(the appositive significance label, the aphorism, the anaphoric run) stay in the
self_review rubric, because a detector that cannot find one instance cannot
count three.
"""

from collections import Counter


def find_budget_overruns(
    findings: list[dict],
    budgets: dict[str, int],
    names: dict[str, str] | None = None,
    budget_only: frozenset[str] = frozenset(),
) -> list[dict]:
    """One finding per budgeted rule that appears more often than its budget.

    `findings` is the already-assembled must_clear list, so this counts what the
    detectors actually reported rather than re-running them. For a rule in
    `budget_only` the instances are dropped from the report by the caller, so
    the overrun carries their excerpts instead: the writer still needs to find
    them.
    """
    names = names or {}
    counts = Counter(
        f["id"] for f in findings if isinstance(f, dict) and f.get("id") in budgets
    )
    out: list[dict] = []
    for rule_id, count in sorted(counts.items()):
        budget = budgets[rule_id]
        if count <= budget:
            continue
        name = names.get(rule_id, rule_id)
        finding = {
            "type": "document_budget",
            "id": rule_id,
            "name": name,
            "count": count,
            "budget": budget,
            "detail": (
                f"{name} appears {count} times in the text supplied; the "
                f"budget for the whole piece is {budget}. A repeated "
                f"rhetorical shape is the durable tell, not any single use."
            ),
            "fix": (
                "Keep the strongest instance and rewrite the rest. Counted "
                "only within this call, so run the final check on the "
                "assembled document rather than section by section "
                "(caveats.per_section_checks_miss_document_budgets)."
            ),
        }
        if rule_id in budget_only:
            finding["excerpts"] = [
                f.get("excerpt", "") for f in findings
                if isinstance(f, dict) and f.get("id") == rule_id
            ]
        out.append(finding)
    return out


__all__ = ["find_budget_overruns"]
