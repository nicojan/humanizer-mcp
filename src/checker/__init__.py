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
    load_self_review,
)
from src.checker.metrics import (
    burstiness,
    length_metrics_apply,
    segment_uniformity,
    target_stdev,
)
from src.checker.phrases import find_flagged_terms, find_phrases
from src.checker.punctuation import find_comma_splices, find_stacked_marks, find_unterminated
from src.checker.report import assemble_report
from src.checker.structures import (
    find_heuristic_structures,
    find_regex_structures,
    find_rule_of_three_density,
)
from src.checker.util import excerpt


def run_checks(text: str, content_type: str | None = None) -> dict:
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
    must.extend(find_flagged_terms(text, load_flagged_terms()))
    must.extend(find_regex_structures(text, load_regex_structures()))
    must.extend(find_heuristic_structures(text))
    must.extend(find_rule_of_three_density(text))
    must.extend(find_credibility_insistence(text, load_credibility_insistence()))
    budgets, budget_names = load_document_budgets()
    budget_only = load_budget_only_ids()
    overruns = find_budget_overruns(must, budgets, budget_names, budget_only)
    must = [f for f in must if f.get("id") not in budget_only]
    must.extend(overruns)

    # Under content_type "label"/"notes" the numbers are still reported, but the
    # flags are cleared so no consumer reads them as a failure.
    applies = length_metrics_apply(content_type)
    raw = burstiness(text, target_stdev(content_type))
    metrics = {
        **raw,
        "burstiness_flag": applies and raw["burstiness_flag"],
        "length_metrics_apply": applies,
    }
    if metrics["burstiness_flag"]:
        must.append(
            {
                "type": "burstiness",
                "detail": (
                    f"low sentence-length variance "
                    f"(stdev {metrics['length_stdev']} < target "
                    f"{metrics['burstiness_target_stdev']})"
                ),
                "fix": "Vary sentence lengths: mix short and long, add a fragment "
                "or a longer multi-clause sentence.",
            }
        )

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
                    "Humans modulate style between a document's sections; LLMs "
                    "hold one flat fingerprint throughout. Make one section "
                    "terse and another more flowing, varying rhythm and "
                    "sentence length section to section. Or justify if the "
                    "format genuinely requires uniform sections."
                ),
            }
        )

    return assemble_report(hard, must, metrics, manual_review=load_self_review())


__all__ = ["run_checks"]
