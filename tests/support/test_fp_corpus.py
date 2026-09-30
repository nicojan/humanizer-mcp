"""Tests for the shared false-positive sweep helper.

The helper is the thing three rule rounds now depend on to state their bar, so
it needs to be able to FAIL. A helper that silently passes everything is the
`short_corpus_cannot_validate_run_detectors` trap wearing a different hat: the
output of a sweep that found nothing and a sweep that cannot fire is identical.
"""

import pytest

from tests.support import fp_corpus

# eval/corpus/human is the Step-0 calibration corpus and is not redistributed
# here (copyrighted excerpts); see eval/corpus/SOURCES.md to reconstruct it
# from the archived source URLs. Tier 1 tests below need real files to make
# their point (a helper that silently passes everything is a no-op), so they
# skip rather than fail on a clone without the corpus.
_needs_tier1 = pytest.mark.skipif(
    not fp_corpus.tier1_available(),
    reason="human calibration corpus is not redistributed (copyrighted excerpts); "
    "see eval/corpus/SOURCES.md to reconstruct it from the archived source URLs",
)


@_needs_tier1
def test_tier1_files_are_the_calibration_human_corpus():
    files = fp_corpus.tier1_files()
    assert len(files) == 16
    assert all(p.suffix == ".txt" for p in files)
    assert all(p.parent.name == "human" for p in files)


@_needs_tier1
def test_tier1_reads_actual_text():
    # A discriminating control: the helper must be reading prose, not empty files.
    texts = [p.read_text(encoding="utf-8") for p in fp_corpus.tier1_files()]
    assert all(len(t.split()) > 50 for t in texts)


def test_assert_tier1_clear_passes_for_a_rule_that_never_fires():
    fp_corpus.assert_tier1_clear(lambda text: [], "FAKE-000")


@_needs_tier1
def test_assert_tier1_clear_fails_for_a_rule_that_does_fire():
    """The control that proves the helper is not a no-op."""
    with pytest.raises(AssertionError) as exc:
        fp_corpus.assert_tier1_clear(lambda text: [{"excerpt": text[:20]}], "FAKE-999")
    assert "FAKE-999" in str(exc.value)


@_needs_tier1
def test_assert_tier1_clear_names_the_offending_file():
    def fires_on_one(text):
        return [{"excerpt": "x"}] if "Chancery" in text or True else []

    with pytest.raises(AssertionError) as exc:
        fp_corpus.assert_tier1_clear(fires_on_one, "FAKE-001")
    assert ".txt" in str(exc.value) or "human_" in str(exc.value)


def test_tier2_rate_is_per_10k_sentences():
    rate = fp_corpus.rate_per_10k(47)
    assert rate == pytest.approx(47 * 10000 / fp_corpus.TIER2_SENTENCES, rel=1e-9)


def test_tier2_bar_threshold_is_the_documented_five_per_10k():
    assert fp_corpus.TIER2_MAX_RATE == 5.0


def test_tier2_bar_accepts_and_rejects_around_the_threshold():
    # 5.0 per 10k on 47,088 sentences is 23.5 firings.
    assert fp_corpus.tier2_within_bar(23)
    assert not fp_corpus.tier2_within_bar(24)


def test_tier2_sentence_count_matches_the_manifest():
    from eval.fpcorpus.manifest import TIER2_SENTENCES

    assert fp_corpus.TIER2_SENTENCES == TIER2_SENTENCES


@pytest.mark.skipif(not fp_corpus.tier2_available(), reason="Tier 2 corpus not fetched")
def test_tier2_files_match_the_recorded_manifest():
    from eval.fpcorpus.manifest import WORKS

    assert len(fp_corpus.tier2_files()) == len(WORKS)


@pytest.mark.skipif(not fp_corpus.tier2_available(), reason="Tier 2 corpus not fetched")
def test_tier2_sweep_reproduces_the_recorded_sentence_count():
    from src.checker.segment import split_sentences

    total = sum(
        len(split_sentences(p.read_text(encoding="utf-8")))
        for p in fp_corpus.tier2_files()
    )
    assert total == fp_corpus.TIER2_SENTENCES
