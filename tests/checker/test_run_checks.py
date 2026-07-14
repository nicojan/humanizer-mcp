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


def test_low_burstiness_surfaces_as_must_clear():
    t = " ".join(["The system processes the incoming data quickly every time."] * 5)
    r = run_checks(t, "prose")
    assert any(m.get("type") == "burstiness" for m in r["must_clear"])


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
