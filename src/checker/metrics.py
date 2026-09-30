"""Burstiness statistics (sentence-length variance). Stdlib only."""

import re
import statistics

from src.checker.segment import split_sentences

_PARA_SPLIT = re.compile(r"\n\s*\n")

# Cross-segment uniformity thresholds. A flag requires BOTH a tight spread of
# per-segment mean sentence lengths (sections read alike) AND low internal
# variance in every segment (each section is itself flat). Conservative by
# design: it should fire on genuinely uniform multi-section text, not on a
# document that merely happens to have balanced section averages.
SEGMENT_MEAN_SPREAD_MAX = 2.5
SEGMENT_INTERNAL_STDEV_MAX = 3.0
MIN_SENTENCES_PER_SEGMENT = 3
MIN_SEGMENTS = 3

_TARGETS = {
    "prose": 6.0,
    "general_prose": 6.0,
    "general": 6.0,
    "academic": 5.0,
    "marketing": 7.0,
    "tech": 4.0,
    "technical": 4.0,
}


# Content types whose caller declares the input is labels, worksheet cells or
# notes, where sentence-length variance is undefined or deliberately flat
# (caveats.metrics_do_not_apply_to_label_text). An explicit opt-in, never
# inferred from the text: guessing "this is labels" from length would misfire on
# real short-form prose.
SHORT_COPY_TYPES = frozenset({"label", "labels", "notes"})


def length_metrics_apply(content_type: str | None) -> bool:
    return (content_type or "prose").lower() not in SHORT_COPY_TYPES


def target_stdev(content_type: str | None) -> float:
    return _TARGETS.get((content_type or "prose").lower(), 6.0)


def burstiness(text: str, target: float) -> dict:
    lengths = [len(s.split()) for s in split_sentences(text)]
    if len(lengths) < 2:
        return {
            "sentence_count": len(lengths),
            "length_mean": float(lengths[0]) if lengths else 0.0,
            "length_stdev": 0.0,
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "burstiness_target_stdev": target,
            "burstiness_flag": False,
        }
    stdev = statistics.pstdev(lengths)
    return {
        "sentence_count": len(lengths),
        "length_mean": round(statistics.mean(lengths), 1),
        "length_stdev": round(stdev, 1),
        "min": min(lengths),
        "max": max(lengths),
        "burstiness_target_stdev": target,
        "burstiness_flag": stdev < target,
    }


def segment_uniformity(text: str) -> dict:
    """Measure whether style stays flat across a document's sections.

    Humans modulate their stylistic fingerprint between a document's intro,
    body, and conclusion; LLMs hold one fingerprint throughout (Kuznetsov et
    al., arXiv:2501.19301). We split on blank lines, keep segments with at least
    MIN_SENTENCES_PER_SEGMENT sentences, and flag when there are at least
    MIN_SEGMENTS of them, their mean sentence lengths barely differ, and each is
    internally flat. Returns a metrics dict; uniformity_flag drives a must_clear.
    """
    paragraphs = [p for p in _PARA_SPLIT.split(text.strip()) if p.strip()]
    segments: list[tuple[float, float]] = []
    for para in paragraphs:
        sentences = split_sentences(para)
        if len(sentences) < MIN_SENTENCES_PER_SEGMENT:
            continue
        lengths = [len(s.split()) for s in sentences]
        segments.append((statistics.mean(lengths), statistics.pstdev(lengths)))

    if len(segments) < MIN_SEGMENTS:
        return {"segment_count": len(segments), "uniformity_flag": False}

    means = [m for m, _ in segments]
    spread = max(means) - min(means)
    max_internal_stdev = max(sd for _, sd in segments)
    flag = (
        spread < SEGMENT_MEAN_SPREAD_MAX
        and max_internal_stdev < SEGMENT_INTERNAL_STDEV_MAX
    )
    return {
        "segment_count": len(segments),
        "segment_mean_lengths": [round(m, 1) for m in means],
        "segment_mean_spread": round(spread, 1),
        "max_internal_stdev": round(max_internal_stdev, 1),
        "uniformity_flag": flag,
    }
