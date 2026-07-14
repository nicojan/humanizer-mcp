"""Assembles the compliance report. prohibitions_clear is gated solely on the
absence of hard_violations."""

_MANUAL_REVIEW = [
    "AR-001: confirm meaning, claims, numbers, names, and stance are unchanged from the source.",
    "Tone and stance preserved (server cannot verify).",
    "Reused rhetorical SHAPE: the same construction (e.g. an antithesis or a copula maxim) restated across the document reads as a tic even when the words differ. Rule-of-three density and cross-section uniformity are now auto-detected (see must_clear); the repeated-shape case is not.",
    "Rhythm uniformity beyond sentence length, and section closers that all land on a short copula maxim (server cannot verify).",
    "Abstraction-as-agent: an abstract noun ('the gap', 'the craft', 'the work', 'the order') used as the subject of an agentive or experiential verb (mattered, decided, kept, taught, carries), so the sentence reads fluent but no one is actually doing anything. Prefer a human or concrete subject (server cannot verify reliably; see AP-033).",
    "Perplexity not measured server-side. Note: local word-level unpredictability and section-to-section variation are the most durable human signals; surface word swaps alone are necessary but not sufficient.",
]

_NEXT_ACTION = (
    "Resolve every hard_violation (required). Rewrite or justify each must_clear "
    "item, and re-run humanizer_check_text until prohibitions_clear is true. Then "
    "run the self-review rubric (manual_review) against your own draft — rate each "
    "item and rewrite every weak spot — before returning."
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
    # the data-driven rubric (data/self_review.json); the static fallback keeps
    # direct callers (and tests) working without the data layer.
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
