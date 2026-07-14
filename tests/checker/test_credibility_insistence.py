"""PR2-#1: reality-assertion / credibility-insistence density. A writer who
repeatedly insists their own account is real/actual/genuine is exhibiting a
defensive credibility hedge; the DENSITY of the token set is the signal, not any
single use. Surfaced as must_clear, never hard. Exclusions keep legitimate uses
(real-time, real estate, quoted text, one sentence-initial 'actually') quiet."""

from src.checker import run_checks
from src.checker.insistence import find_credibility_insistence
from src.checker.loader import load_credibility_insistence

CONFIG = load_credibility_insistence()


def _find(text):
    return find_credibility_insistence(text, CONFIG)

# The in-the-wild example: seven "real" in ~60 words, all passed the old checker.
WILD = (
    "A real engagement, mid-build. Each board was detailed and real. "
    "The second draft is the real one. But the design is real. "
    "My first real service-design project. I mapped the real flow. "
    "It runs when a real build has to run in reverse."
)


def test_repeated_token_fires():
    res = _find(WILD)
    assert len(res) == 1
    assert res[0]["type"] == "credibility_insistence"


def test_single_use_does_not_fire():
    assert _find(
        "This was a real engagement, mid-build, and it went well in the end."
    ) == []


def test_two_uses_in_long_text_does_not_fire():
    filler = "We shipped steadily through the quarter and the small team held together. " * 40
    text = "This was a real engagement. " + filler + " The design is real."
    assert _find(text) == []


def test_real_time_and_real_estate_are_excluded():
    text = (
        "We built a real-time pipeline for a real estate firm. The real-time sync "
        "mattered most. Real estate data is messy. A real-time dashboard helped here. "
        "Real-time syncing again at the end."
    )
    assert _find(text) == []


def test_interrogative_really_and_quoted_tokens_excluded():
    text = 'She asked, "is it really?" He quoted the word "real" twice. Really? Really?'
    assert _find(text) == []


def test_set_diversity_density_fires():
    # No single token hits 3x, but the SET is dense: real + actually + genuine +
    # truly across a short passage exceeds ~2 per 400 words.
    text = (
        "We mapped the actual flow of the build. The result felt genuine to the team, "
        "and the prototype truly worked the way the client wanted it to work in the end."
    )
    res = _find(text)
    assert len(res) == 1
    assert res[0]["type"] == "credibility_insistence"


def test_surfaces_through_run_checks():
    r = run_checks(WILD, "prose")
    assert any(m.get("type") == "credibility_insistence" for m in r["must_clear"])
    assert not any(
        v.get("type") == "credibility_insistence" for v in r["hard_violations"]
    )
