"""BS-021 noun_participle_fragment: a verbless 'Noun, past-participle.' sentence
('The same board, rebuilt.'). Regex banned_structure, surfaces as must_clear
(checklist), never hard. Positive cases plus the false-positive guards."""

from src.checker import run_checks


def _names(r):
    return {m.get("name") for m in r["must_clear"]}


def _no_hard_structure(r):
    return not any(v.get("type") == "banned_structure" for v in r["hard_violations"])


# --- fires -------------------------------------------------------------------


def test_fires_on_irregular_participle():
    # The reviewer's exact in-the-wild example (irregular participle, not -ed).
    r = run_checks("The same board, rebuilt.", "prose")
    assert "noun_participle_fragment" in _names(r)
    assert _no_hard_structure(r)


def test_fires_on_regular_ed_participle():
    r = run_checks("The homepage, reimagined.", "prose")
    assert "noun_participle_fragment" in _names(r)
    assert _no_hard_structure(r)


def test_fires_mid_document_after_a_real_sentence():
    # Sentence-initial determiner after a terminal mark, not only at text start.
    r = run_checks("We shipped the redesign. The whole system, rewritten.", "prose")
    assert "noun_participle_fragment" in _names(r)


# --- false-positive guards ---------------------------------------------------


def test_skips_non_initial_determiner():
    # 'the room' is not sentence-initial: a legitimate depiction, not the tell.
    r = run_checks("He left the room, defeated.", "prose")
    assert "noun_participle_fragment" not in _names(r)


def test_skips_full_sentence_with_finite_verb():
    # Participle sits inside a full clause; the sentence has a real main verb.
    for t in (
        "The board, which we rebuilt, is live.",
        "The report, revised, was sent.",
    ):
        r = run_checks(t, "prose")
        assert "noun_participle_fragment" not in _names(r), t


def test_skips_participle_with_tail():
    # Participle is not the last token, so it is not the bare fragment.
    r = run_checks("The summit, held annually.", "prose")
    assert "noun_participle_fragment" not in _names(r)


def test_skips_short_ed_lookalikes():
    # 'red' / 'bed' end in 'ed' but are not participles; the length floor guards them.
    for t in ("The wall, red.", "The dog, fed."):
        r = run_checks(t, "prose")
        assert "noun_participle_fragment" not in _names(r), t


def test_skips_comma_less_idiom():
    # Fixed expressions lack the defining comma and the determiner-led subject.
    for t in ("Case closed.", "Mission accomplished."):
        r = run_checks(t, "prose")
        assert "noun_participle_fragment" not in _names(r), t
