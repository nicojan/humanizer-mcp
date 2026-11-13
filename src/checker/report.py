"""Assembles the compliance report. prohibitions_clear is gated solely on the
absence of hard_violations."""

# Generic fallback for direct callers that pass no rubric. run_checks always
# passes the data rubric (data/self_review.json) through rubric_lines.
_MANUAL_REVIEW = [
    "Check that the draft keeps the meaning, claims, numbers, names and stance of the source.",
    "Read the draft as a cold reader would and rewrite any sentence that reader could not follow on first read.",
    'Run the last check on the assembled document with rubric="full" and do the full self-review.',
]

_NEXT_ACTION = (
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

_NOTE = (
    "prohibitions_clear means no hard prohibitions remain. It does NOT mean "
    "humanization is complete."
)


def assemble_report(
    hard_violations: list[dict],
    must_clear: list[dict],
    metrics: dict,
    manual_review: list[str] | None = None,
) -> dict:
    # manual_review is the human-likeness self-review rubric. run_checks passes
    # the data rubric's short or full lines; the generic fallback keeps direct
    # callers (and tests) working without the data layer.
    review = manual_review if manual_review is not None else list(_MANUAL_REVIEW)
    return {
        "prohibitions_clear": len(hard_violations) == 0,
        "note": _NOTE,
        "hard_violations": hard_violations,
        "must_clear": must_clear,
        "metrics": metrics,
        "manual_review": review,
        "next_action": _NEXT_ACTION,
    }
