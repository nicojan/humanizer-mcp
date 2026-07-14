"""Group E: cross-segment style uniformity. LLMs hold one flat stylistic
fingerprint across a document's intro/body/conclusion; humans modulate style
between segments (Kuznetsov et al., arXiv:2501.19301, EMNLP 2025 — verified). We
flag conservatively: only when there are >=3 multi-sentence segments AND each is
internally flat AND their mean sentence lengths barely differ. Surfaced as a
must_clear ('rewrite or justify'), mirroring the burstiness check."""

from src.checker import run_checks
from src.checker.metrics import segment_uniformity

# Three paragraphs, each four near-identical-length SVO sentences: a flat
# fingerprint held across all segments.
UNIFORM = "\n\n".join(
    [
        " ".join(["The system processes each incoming record in the queue."] * 4),
        " ".join(["The service handles every pending request in strict order."] * 4),
        " ".join(["The program updates the relevant table after each change."] * 4),
    ]
)

# Three paragraphs that vary length within and across segments, with a fragment.
VARIED = "\n\n".join(
    [
        "We shipped Tuesday. The rollout was quiet, almost anticlimactic after "
        "weeks of dread. Nobody cheered.",
        "Then the tickets started. Dozens of them. Each one a small fire that "
        "needed putting out before the next arrived, and they kept arriving well "
        "past midnight while the on-call engineer worked alone.",
        "By Friday it had settled. Mostly. We never did find the root cause.",
    ]
)


def test_uniform_multiparagraph_is_flagged():
    assert segment_uniformity(UNIFORM)["uniformity_flag"] is True


def test_varied_multiparagraph_is_not_flagged():
    assert segment_uniformity(VARIED)["uniformity_flag"] is False


def test_single_paragraph_is_never_flagged():
    m = segment_uniformity("One short paragraph here. It has only two sentences.")
    assert m["uniformity_flag"] is False
    assert m["segment_count"] < 3


def test_uniformity_surfaces_through_run_checks():
    r = run_checks(UNIFORM, "prose")
    assert any(m.get("type") == "segment_uniformity" for m in r["must_clear"])


def test_varied_text_has_no_segment_uniformity_finding():
    r = run_checks(VARIED, "prose")
    assert not any(m.get("type") == "segment_uniformity" for m in r["must_clear"])
