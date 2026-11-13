"""Deterministic humanization checker (no LLM, no server-state mutation)."""

from src.checker.budgets import find_budget_overruns
from src.checker.emdash import find_emdashes
from src.checker.insistence import find_credibility_insistence
from src.checker.loader import (
    load_budget_only_ids,
    load_credibility_insistence,
    load_document_budgets,
    load_flagged_terms,
    load_hard_phrases,
    load_regex_structures,
    load_terms_of_art,
)
from src.checker.metrics import (
    length_metrics_apply,
    list_measures_apply,
    segment_uniformity,
    sentence_length_stats,
)
from src.checker.phrases import find_flagged_terms, find_phrases
from src.checker.punctuation import find_comma_splices, find_stacked_marks, find_unterminated
from src.checker.report import assemble_report
from src.checker.rubric import RubricMode, rubric_lines
from src.checker.structures import (
    find_heuristic_structures,
    find_regex_structures,
    find_rule_of_three_density,
)
from src.checker.util import excerpt


def run_checks(
    text: str, content_type: str | None = None, rubric: RubricMode = "short"
) -> dict:
    hard: list[dict] = find_emdashes(text)
    hard.extend(find_stacked_marks(text))
    for phrase, off in find_phrases(text, load_hard_phrases()):
        hard.append(
            {
                "rule": "banned_structure",
                "type": "fixed_phrase",
                "phrase": phrase,
                "offset": off,
                "excerpt": excerpt(text, off, off + len(phrase)),
                "fix": "Cut the phrase; state the point directly.",
            }
        )

    must: list[dict] = []
    must.extend(find_unterminated(text))
    must.extend(find_comma_splices(text))
    must.extend(find_flagged_terms(text, load_flagged_terms(), load_terms_of_art()))
    must.extend(find_regex_structures(text, load_regex_structures()))
    must.extend(find_heuristic_structures(text))
    if list_measures_apply(content_type):
        must.extend(find_rule_of_three_density(text))
    must.extend(find_credibility_insistence(text, load_credibility_insistence()))
    budgets, budget_names = load_document_budgets()
    budget_only = load_budget_only_ids()
    overruns = find_budget_overruns(must, budgets, budget_names, budget_only)
    must = [f for f in must if f.get("id") not in budget_only]
    must.extend(overruns)

    # Sentence-length numbers are reported, never turned into a finding or a
    # target. Under content_type "label"/"notes"/"resume" they are marked as not
    # applying so no consumer reads them as a failure.
    applies = length_metrics_apply(content_type)
    raw = sentence_length_stats(text)
    metrics = {**raw, "length_metrics_apply": applies}

    raw_segments = segment_uniformity(text)
    segments = {**raw_segments, "uniformity_flag": applies and raw_segments["uniformity_flag"]}
    metrics = {**metrics, "segment_variation": segments}
    if segments["uniformity_flag"]:
        must.append(
            {
                "type": "segment_uniformity",
                "detail": (
                    f"style is flat across {segments['segment_count']} sections "
                    f"(mean sentence-length spread "
                    f"{segments['segment_mean_spread']} words)"
                ),
                "fix": (
                    "Every section reads in the same rhythm and sentence length, "
                    "which can mean the text was written to one template. Check "
                    "each section against its own job and let its texture follow "
                    "that job. Do not make sections differ for contrast. If the "
                    "format needs uniform sections, say so and leave them."
                ),
            }
        )

    return assemble_report(
        hard, must, metrics, manual_review=rubric_lines(content_type, rubric)
    )


__all__ = ["run_checks"]
