"""Content profiles for case-study and résumé copy, plus terms of art.

Round: 2026-11-09. Spec:
docs/superpowers/specs/2026-11-09-case-study-and-resume-profiles.md

Two registers kept producing findings that a portfolio project excused by hand
on every audit: rule_of_three_density on a résumé's Skills block (a list is the
format) and the flagged term "differentiate" inside "differentiated
instruction" (a teaching term with no plainer equivalent). This round adds a
`resume` content type that turns off the list and length measures, a data-driven
terms-of-art allowlist that applies to every content type, and two content
profiles (`case_study`, `resume`) carrying the guidance from that project's
copy reviews. Every change removes findings; nothing new is detected.
"""

import json
import pathlib

import pytest

from src.checker import run_checks
from src.checker.loader import load_terms_of_art
from src.tools.read import _resolve_content_type

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

SKILLS = (
    "Design: user research, journey mapping, and usability testing.\n"
    "Prototyping: Figma, Framer, and HTML, CSS and JavaScript.\n"
    "Teaching: curriculum design, assessment, and differentiated instruction."
)


def _types(report: dict) -> list[str]:
    return [f.get("type") for f in report["must_clear"]]


def _terms(report: dict) -> list[str]:
    return [f["term"] for f in report["must_clear"] if f.get("type") == "flagged_term"]


# ---------------------------------------------------------------------------
# Terms of art: every content type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "I taught with differentiated instruction for ten years.",
        "Differentiated learning plans for every student.",
        "She plans differentiated lessons and differentiated assessment.",
    ],
)
def test_a_term_of_art_is_not_flagged(text):
    assert "differentiate" not in _terms(run_checks(text))


@pytest.mark.parametrize(
    "text",
    [
        "Our product differentiates itself through design.",
        "We need to differentiate the brand.",
        "Differentiated by its speed, the tool wins.",
    ],
)
def test_the_word_outside_the_term_is_still_flagged(text):
    assert "differentiate" in _terms(run_checks(text))


def test_only_the_protected_occurrence_is_dropped():
    text = "I use differentiated instruction. Our product differentiates itself."
    found = [f for f in run_checks(text)["must_clear"] if f.get("term") == "differentiate"]
    assert len(found) == 1 and found[0]["count"] == 1
    assert found[0]["locations"] == [text.lower().index("differentiates")]


def test_terms_of_art_load_from_data():
    terms = load_terms_of_art()
    assert "differentiated instruction" in terms
    assert all(t == t.lower() for t in terms)


# ---------------------------------------------------------------------------
# content_type="resume"
# ---------------------------------------------------------------------------


def test_a_skills_block_trips_rule_of_three_as_prose():
    """The control: without the declaration, the density finding fires."""
    assert "rule_of_three_density" in _types(run_checks(SKILLS))


@pytest.mark.parametrize("ct", ["resume", "résumé", "cv", "CV", "Resume"])
def test_resume_turns_off_list_and_length_measures(ct):
    report = run_checks(SKILLS, content_type=ct)
    assert "rule_of_three_density" not in _types(report)
    assert report["metrics"]["length_metrics_apply"] is False
    assert "burstiness" not in _types(report)


def test_resume_leaves_every_other_layer_running():
    text = "I delve into user research. Tutoring stays. Built the platform — solo."
    report = run_checks(text, content_type="resume")
    assert report["hard_violations"], "AR-002 must still be hard"
    assert "delve" in _terms(report)
    assert any(f.get("id") == "BS-053" for f in report["must_clear"])


def test_case_study_runs_as_prose():
    a = run_checks(SKILLS, content_type="case_study")
    b = run_checks(SKILLS)
    assert a["must_clear"] == b["must_clear"]
    assert a["metrics"]["length_metrics_apply"] is True


# ---------------------------------------------------------------------------
# The two profiles
# ---------------------------------------------------------------------------

LAYERS = {"lexical_patterns", "structural_patterns", "sentiment_tone", "discourse_cohesion", "psycholinguistic_texture"}


def _profiles() -> dict:
    return json.loads((DATA / "content_profiles.json").read_text())["profiles"]


@pytest.mark.parametrize("key", ["case_study", "resume"])
def test_profile_has_the_shape_of_the_others(key):
    profile = _profiles()[key]
    assert set(_profiles()["marketing"]) <= set(profile), set(_profiles()["marketing"]) - set(profile)
    assert set(profile["layer_adjustments"]) == LAYERS
    used = {
        layer["aggressiveness"]
        for other in _profiles().values()
        for layer in other["layer_adjustments"].values()
    }
    for layer in profile["layer_adjustments"].values():
        assert layer["aggressiveness"] in used
        assert layer["notes"].strip()
    assert profile["special_considerations"]


@pytest.mark.parametrize(
    "alias,key",
    [
        ("case_study", "case_study"),
        ("case-study", "case_study"),
        ("portfolio", "case_study"),
        ("product", "case_study"),
        ("resume", "resume"),
        ("résumé", "resume"),
        ("cv", "resume"),
        ("CV", "resume"),
    ],
)
def test_aliases_resolve(alias, key):
    assert _resolve_content_type(alias, _profiles()) == key


def test_profiles_carry_the_review_findings():
    case = json.dumps(_profiles()["case_study"])
    resume = json.dumps(_profiles()["resume"])
    for phrase in ("never used the product", "one UX", "so a fix reached people"):
        assert phrase in case, phrase
    for phrase in ("Skills", "differentiated instruction", "keep the Figma files behind them tidy"):
        assert phrase in resume, phrase
