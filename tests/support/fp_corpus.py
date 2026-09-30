"""Shared false-positive sweep helper for the two eval corpus tiers.

Before this module, `test_no_false_positives_on_human_corpus` was
re-implemented independently in three rule-round test files, which left each
round's bar implicit in its own file and gave a new round nowhere to say which
corpus it was standing on.

Two tiers, two metrics. The reasoning is in
`docs/superpowers/specs/2026-09-18-two-tier-fp-corpus-and-revised-bar.md`.

Tier 1 (`eval/corpus/human`): 16 files, 109 sentences, four modern genres.
    Bar: ZERO findings from the round's new rules, every file.
    Blind to anything needing three or more consecutive sentences or sections.

Tier 2 (`eval/fpcorpus/longform`): six pre-1930 works, 47,088 sentences.
    Bar: at most 5.0 findings per 10k sentences, AND every firing read and
    judged, with the precision fraction reported.
    Blind to modern promotional and technical register.

Tier 2 is opt-in: `python -m eval.fpcorpus.fetch_longform`. Helpers report
absence so callers can skip, because a clean clone has no Tier 2 corpus.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

from eval.fpcorpus.manifest import TIER2_SENTENCES

_REPO_ROOT = Path(__file__).resolve().parents[2]

TIER1_DIR = _REPO_ROOT / "eval" / "corpus" / "human"
TIER2_DIR = _REPO_ROOT / "eval" / "fpcorpus" / "longform"

# Tier 2 threshold. Set by what one person can audit rather than by curve
# fitting: 5.0 per 10k of 47,088 sentences is about 24 firings, which is
# readable in a sitting. The rate decides whether the reading is feasible; the
# reading is the bar.
TIER2_MAX_RATE = 5.0

HitsFn = Callable[[str], Sequence[object]]


def tier1_files() -> list[Path]:
    return sorted(TIER1_DIR.glob("*.txt"))


def tier1_available() -> bool:
    """False in this public export: eval/corpus/human is the Step-0
    calibration corpus and is not redistributed (copyrighted excerpts). See
    eval/corpus/SOURCES.md to reconstruct it from the archived source URLs."""
    return bool(tier1_files())


def tier2_files() -> list[Path]:
    return sorted(TIER2_DIR.glob("pg*.txt"))


def tier2_available() -> bool:
    return bool(tier2_files())


def assert_tier1_clear(hits: HitsFn, rule: str) -> None:
    """Tier 1 bar: `rule` must return no hits on any calibration human file."""
    for path in tier1_files():
        found = hits(path.read_text(encoding="utf-8"))
        assert not found, f"{rule} false positive in {path.name}: {list(found)[:3]}"


def tier1_findings(hits: HitsFn) -> dict[str, list[object]]:
    """Every Tier 1 file with at least one hit. For reporting rather than
    asserting: the sweep is NOT clean on Tier 1 today. The banned_structures
    layer returns 1 finding (a standing BS-011), adding rule_of_three_density
    makes it 2 in 2 files, and adding the lexicon makes it 12 in 9. That is why
    the bar is scoped to a round's own new rules rather than to a full sweep."""
    out: dict[str, list[object]] = {}
    for path in tier1_files():
        found = list(hits(path.read_text(encoding="utf-8")))
        if found:
            out[path.name] = found
    return out


def rate_per_10k(count: int) -> float:
    """Findings per 10k Tier 2 sentences. The denominator is recorded in the
    manifest and is large, so a raw count is not comparable across rounds."""
    return count * 10000 / TIER2_SENTENCES


def tier2_within_bar(count: int) -> bool:
    return rate_per_10k(count) <= TIER2_MAX_RATE


def tier2_sweep(hits: HitsFn) -> tuple[int, float, dict[str, int]]:
    """Run `hits` over every Tier 2 work.

    Returns the total firing count, the rate per 10k sentences, and the count
    per work. Every firing is a false positive by construction, because the
    corpus is unambiguously human.

    Callers must still read the firings. A rate inside the bar does not clear a
    rule whose firings turn out to be legitimate prose: that is exactly how the
    anaphora chain was rejected at 3.2 per 10k.
    """
    per_work: dict[str, int] = {}
    total = 0
    for path in tier2_files():
        n = len(hits(path.read_text(encoding="utf-8")))
        per_work[path.stem] = n
        total += n
    return total, rate_per_10k(total), per_work


__all__ = [
    "TIER1_DIR",
    "TIER2_DIR",
    "TIER2_MAX_RATE",
    "TIER2_SENTENCES",
    "assert_tier1_clear",
    "rate_per_10k",
    "tier1_available",
    "tier1_files",
    "tier1_findings",
    "tier2_available",
    "tier2_files",
    "tier2_sweep",
    "tier2_within_bar",
]
