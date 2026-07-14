"""PR2 #2/#3/#5/#6: four new banned structures from the in-the-wild audit.
All surface as must_clear (checklist), never hard. Each has a positive case and
false-positive guards."""

from src.checker import run_checks


def _names(r):
    return {m.get("name") for m in r["must_clear"]}


def _no_hard_structure(r):
    return not any(v.get("type") == "banned_structure" for v in r["hard_violations"])


# --- PR2-#2 BS-017 disclaimer_reversal ---------------------------------------


def test_disclaimer_reversal_fires():
    r = run_checks(
        "I will not claim numbers I have not measured. But the design is real.",
        "prose",
    )
    assert "disclaimer_reversal" in _names(r)
    assert _no_hard_structure(r)


def test_disclaimer_reversal_skips_plain_but():
    # A 'But' that does not follow a disclaiming verb must not fire.
    r = run_checks("We shipped on Tuesday. But it broke on Wednesday.", "prose")
    assert "disclaimer_reversal" not in _names(r)


# --- PR2-#3 BS-018 copula_maxim_closer ---------------------------------------


def test_copula_maxim_closer_fires():
    r = run_checks(
        "We tried three layouts and threw two away. The craft is mostly restraint.",
        "prose",
    )
    assert "copula_maxim_closer" in _names(r)
    assert _no_hard_structure(r)


def test_copula_maxim_closer_skips_concrete_closer():
    # Concrete subject + concrete predicate is not an abstract maxim.
    r = run_checks(
        "We tried three layouts and threw two away. The meeting starts at noon on Friday.",
        "prose",
    )
    assert "copula_maxim_closer" not in _names(r)


# --- PR2-#5 BS-019 locative_pseudocleft --------------------------------------


def test_locative_pseudocleft_fires():
    r = run_checks(
        "The gap between those two facts was where the work kept getting lost.",
        "prose",
    )
    assert "locative_pseudocleft" in _names(r)
    assert _no_hard_structure(r)


def test_locative_pseudocleft_skips_demonstrative_subjects():
    # The high-frequency benign forms must stay quiet.
    for t in (
        "This is how we shipped it.",
        "Here is where you sign the form.",
        "That was when everything changed for us.",
    ):
        r = run_checks(t, "prose")
        assert "locative_pseudocleft" not in _names(r), t


# --- PR2-#6 BS-020 verb_antithesis_pair --------------------------------------


def test_verb_antithesis_pair_fires_on_mirrored_verb():
    r = run_checks("AI carries the busywork. It never carries the judgment.", "prose")
    assert "verb_antithesis_pair" in _names(r)
    assert _no_hard_structure(r)


def test_verb_antithesis_pair_skips_unrelated_negation():
    # 'It never finished' does not mirror a verb from the prior sentence.
    r = run_checks("I ran the migration overnight. It never finished.", "prose")
    assert "verb_antithesis_pair" not in _names(r)


def test_verb_antithesis_pair_matches_inflected_verb():
    # The stem fallback should still catch carry/carries across the pair.
    r = run_checks("People carry the load. It never carries the blame.", "prose")
    assert "verb_antithesis_pair" in _names(r)
