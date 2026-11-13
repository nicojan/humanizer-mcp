import re

from src.checker import run_checks


def test_emdash_blocks_prohibitions():
    r = run_checks("The plan — bold — failed.", "prose")
    assert r["prohibitions_clear"] is False
    assert any(v["type"] == "em_dash" for v in r["hard_violations"])


def test_fixed_phrase_blocks_prohibitions():
    r = run_checks("It is important to note that we shipped on time.", "prose")
    assert r["prohibitions_clear"] is False
    assert any(v["type"] == "fixed_phrase" for v in r["hard_violations"])


def test_clean_text_passes_prohibitions():
    r = run_checks(
        "We shipped the update on Tuesday. The team was tired but glad it landed.",
        "prose",
    )
    assert r["prohibitions_clear"] is True


def test_delve_surfaces_as_must_clear():
    r = run_checks(
        "Let us look at the data. We delve into the quarterly results here today.",
        "prose",
    )
    assert any(m.get("term") == "delve" for m in r["must_clear"])


UNIFORM_TEXT = " ".join(["The system processes the incoming data quickly every time."] * 5)


def test_burstiness_is_never_a_must_clear_finding():
    """Sentence-length variance is a reported number, not a target the writer
    is told to hit. Asking for variation made the model perform it."""
    r = run_checks(UNIFORM_TEXT, "prose")
    assert not any(m.get("type") == "burstiness" for m in r["must_clear"])


def test_metrics_report_lengths_without_a_target():
    m = run_checks(UNIFORM_TEXT, "prose")["metrics"]
    assert "burstiness_flag" not in m and "burstiness_target_stdev" not in m
    assert "length_stdev" in m and "length_mean" in m
    assert m["length_metrics_apply"] is True and "segment_variation" in m


def test_comma_splice_fix_never_recommends_a_colon():
    f = next(
        x for x in run_checks("We shipped the fix, it worked.")["must_clear"]
        if x["type"] == "comma_splice"
    )
    # Word boundary: "semicolon" is the recommended mark and contains "colon".
    assert not re.search(r"\bcolons?\b", f["fix"], re.IGNORECASE)


def test_negative_parallelism_false_positive_is_clearable_not_hard():
    # "It's not just me, but the team agrees" is legitimate prose that matches
    # the BS-006 regex. The design's must_clear-or-justify model requires this
    # to surface as a CLEARABLE candidate, never as a hard violation, or the
    # loop would lock on a false positive and the LLM could not reach
    # prohibitions_clear=true on perfectly fine text.
    r = run_checks("It's not just me, but the team agrees on this.", "prose")
    assert any(m.get("name") == "negative_parallelism" for m in r["must_clear"])
    assert not any(
        v.get("type") == "banned_structure" for v in r["hard_violations"]
    )


def test_comma_splice_surfaces_as_must_clear_not_hard():
    # A comma splice is a real punctuation error (AR-003) but is surfaced as a
    # clearable candidate, never a hard violation — the conservative posture
    # avoids veto-locking on intentional stylistic splices.
    r = run_checks("It was late, we went home.", "prose")
    assert any(m.get("type") == "comma_splice" for m in r["must_clear"])
    assert not any(v.get("type") == "comma_splice" for v in r["hard_violations"])
