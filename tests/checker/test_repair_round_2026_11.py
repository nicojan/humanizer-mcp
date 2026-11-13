"""The 2026-11 repair round: lexicon entries that never fired.

Five terms added on 2026-09-17 were written inside other entries'
`alternatives` arrays (under delve, comprehensive and realm), so
`load_flagged_terms()` never saw them as terms: they never fired, and the guide
served them as replacement suggestions. The round moves them to the top level
and measures each one alone against the standing bar before it ships.

Two guards would have caught the nesting. In tests/data/test_guide_consistency.py,
`test_alternatives_are_plain_strings_that_pass_the_checker` fails on a dict
inside `alternatives`. Here, `test_every_term_entry_in_the_data_is_loaded`
counts term entries in the data file itself, so an entry the loader never
returns is a failure rather than an absence. `test_every_lexicon_term_fires_on_a_sentence_containing_it`
is NOT a nesting guard: it iterates the loader's own output, so it can only
check terms the loader already found.

Measured per term in one run, with `Moreover` as the control and a fresh
sentinel at 0: `nestle`, `renowned`, `diverse array` and `natural beauty` are
inside the bar and ship. `profound` measured 40 firings on Tier 2 (8.5 per
10k), all ordinary literary prose, and is dropped rather than scoped.
"""

import time
from collections.abc import Callable

import pytest

from src.checker import run_checks
from src.checker.budgets import find_budget_overruns
from src.checker.loader import (
    load_budget_only_ids,
    load_document_budgets,
    load_flagged_terms,
    load_hard_phrases,
    load_regex_structures,
    load_terms_of_art,
)
from src.checker.phrases import find_flagged_terms
from src.checker.structures import find_regex_structures
from src.storage.json_store import load_json
from tests.support.fp_corpus import (
    assert_terse_clear,
    assert_tier1_clear,
    tier2_available,
    tier2_sweep,
    tier2_within_bar,
)


def entry(term: str) -> dict:
    """The `load_flagged_terms()` dict for `term` (case-insensitive)."""
    found = next(
        (t for t in load_flagged_terms() if t["term"].lower() == term.lower()), None
    )
    assert found is not None, f"no flagged term {term!r} in load_flagged_terms()"
    return found


# The loader's categories in lexical_patterns.json, and the key that names the
# term in each. Mirrors load_flagged_terms(); a new category must be added both
# there and here, or its entries fail the denominator test below.
TERM_CATEGORIES: dict[tuple[str, ...], str] = {
    ("flagged_verbs",): "ai_word",
    ("flagged_adjectives",): "ai_word",
    ("flagged_nouns",): "ai_word",
    ("flagged_transitions",): "ai_phrase",
    ("flagged_qualifiers", "items"): "ai_phrase",
    ("adverb_patterns", "flagged_ai_adverbs"): "ai_adverb",
    ("nominalization", "common_nominalizations"): "nominal",
}
TERM_KEYS = frozenset(TERM_CATEGORIES.values())


def _category_items(lex: dict, path: tuple[str, ...]) -> list:
    node: object = lex
    for key in path:
        node = node.get(key, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, list) else []


def _term_dicts_anywhere(obj: object) -> list[dict]:
    """Every dict anywhere under obj that carries a term key."""
    if isinstance(obj, dict):
        own = [obj] if TERM_KEYS & obj.keys() else []
        return own + [d for v in obj.values() for d in _term_dicts_anywhere(v)]
    if isinstance(obj, list):
        return [d for v in obj for d in _term_dicts_anywhere(v)]
    return []


def term_entry_defects(lex: dict) -> list[str]:
    """Entries the loader would silently skip: a non-dict item, a missing or
    empty term key, the wrong term key for its category, or a term dict that
    sits anywhere other than directly in a category list (nested)."""
    defects: list[str] = []
    placed: set[int] = set()
    for path, key in TERM_CATEGORIES.items():
        for i, item in enumerate(_category_items(lex, path)):
            where = f"{'.'.join(path)}[{i}]"
            if not isinstance(item, dict):
                defects.append(f"{where}: not an object")
                continue
            placed.add(id(item))
            if not item.get(key):
                defects.append(f"{where}: no '{key}' (keys: {sorted(item)})")
            wrong = (TERM_KEYS - {key}) & item.keys()
            if wrong:
                defects.append(f"{where}: wrong term key {sorted(wrong)} for this category")
    for d in _term_dicts_anywhere(lex):
        if id(d) not in placed:
            name = next(str(d[k]) for k in sorted(TERM_KEYS) if k in d)
            defects.append(f"nested or misplaced term entry: {name!r}")
    return defects


def test_term_entry_defects_control():
    """The denominator check catches each way an entry can be skipped."""
    clean = {"flagged_verbs": [{"ai_word": "delve", "alternatives": ["dig into"]}]}
    nested = {"flagged_verbs": [{"ai_word": "delve", "alternatives": [{"ai_word": "nestle"}]}]}
    wrong_key = {"flagged_verbs": [{"ai_phrase": "delve"}]}
    missing = {"flagged_nouns": [{"word": "realm"}]}
    not_object = {"flagged_nouns": ["realm"]}
    assert term_entry_defects(clean) == []
    assert any("nestle" in d for d in term_entry_defects(nested))
    assert any("wrong term key" in d for d in term_entry_defects(wrong_key))
    assert any("no 'ai_word'" in d for d in term_entry_defects(missing))
    assert any("not an object" in d for d in term_entry_defects(not_object))


def test_lexicon_has_no_skipped_term_entries():
    assert term_entry_defects(load_json("lexical_patterns.json")) == []


def test_every_term_entry_in_the_data_is_loaded():
    """Data-side denominator: every term entry in the file is returned by the
    loader, except the ones promoted to a hard phrase, and the gap is exactly
    that promoted set."""
    lex = load_json("lexical_patterns.json")
    data_terms = [
        str(item[key])
        for path, key in TERM_CATEGORIES.items()
        for item in _category_items(lex, path)
        if isinstance(item, dict) and item.get(key)
    ]
    hard = {p.lower() for p in load_hard_phrases()}
    promoted = sorted(t for t in data_terms if t.lower() in hard)
    loaded = sorted(t["term"] for t in load_flagged_terms())
    assert promoted, "control: some lexicon terms are hard-promoted today"
    assert len(_term_dicts_anywhere(lex)) == len(data_terms)
    assert loaded == sorted(t for t in data_terms if t.lower() not in hard)
    assert len(data_terms) - len(loaded) == len(promoted)


@pytest.mark.parametrize("t", load_flagged_terms(), ids=lambda t: t["term"])
def test_every_lexicon_term_fires_on_a_sentence_containing_it(t):
    found = find_flagged_terms(f"They wrote {t['term']} in the draft.", [t], [])
    assert found, t["term"]


POSITIVES = {
    "nestle": "The cabin is nestled in the pines.",
    "profound": "The policy had a profound impact on families.",
    "renowned": "A renowned chef runs the kitchen.",
    "diverse array": "The menu offers a diverse array of dishes.",
    "natural beauty": "Visitors come for the natural beauty of the coast.",
}


SHIPPED_TERMS = ["diverse array", "natural beauty", "nestle", "renowned"]

# Dropped on measurement: term -> the one-line reason.
DROPPED_TERMS = {
    "profound": "8.5 per 10k on Tier 2, all legitimate ('profound silence', "
    "'profound darkness'), and it flags condolence prose",
}


@pytest.mark.parametrize("term", SHIPPED_TERMS)
def test_september_lexicon_term_fires(term):
    found = {
        f["term"].lower()
        for f in run_checks(POSITIVES[term])["must_clear"]
        if f.get("type") == "flagged_term"
    }
    assert term in found


def term_hits(term_entry: dict) -> Callable[[str], list[int]]:
    """A corpus-sweep hits function for one lexicon entry: one item per
    occurrence. `find_flagged_terms` returns at most one finding per term per
    text (with `count` and `locations`), and `tier2_sweep` counts items, so
    returning the findings would cap a whole Tier 2 work at one firing."""

    def hits(text: str) -> list[int]:
        found = find_flagged_terms(text, [term_entry], load_terms_of_art())
        return [loc for f in found for loc in f["locations"]]

    return hits


_NEEDS_TIER2 = pytest.mark.skipif(
    not tier2_available(),
    reason="Tier 2 corpus absent: python -m eval.fpcorpus.fetch_longform",
)


@pytest.mark.parametrize("term", SHIPPED_TERMS)
def test_moved_term_meets_the_bar(term):
    hits = term_hits(entry(term))
    assert_tier1_clear(hits, term)
    assert_terse_clear(hits, term)


@_NEEDS_TIER2
@pytest.mark.parametrize("term", SHIPPED_TERMS)
def test_moved_term_is_within_the_tier2_bar(term):
    assert tier2_within_bar(tier2_sweep(term_hits(entry(term)))[0])


@_NEEDS_TIER2
def test_tier2_harness_fails_a_known_bad_term_and_passes_a_sentinel():
    """The Tier 2 leg above means nothing unless the same harness can fail.
    `profound` was dropped at 40 firings; a never-occurring nonce must be 0."""
    bad = {"term": "profound", "severity": "moderate", "alternatives": []}
    sentinel = {"term": "zh" + "ovrequin", "severity": "low", "alternatives": []}
    assert not tier2_within_bar(tier2_sweep(term_hits(bad))[0])
    assert tier2_sweep(term_hits(sentinel))[0] == 0


@pytest.mark.parametrize("term", sorted(DROPPED_TERMS))
def test_dropped_term_is_not_flagged(term):
    assert term not in {t["term"].lower() for t in load_flagged_terms()}, DROPPED_TERMS[term]
    assert term not in {
        f["term"].lower()
        for f in run_checks(POSITIVES[term])["must_clear"]
        if f.get("type") == "flagged_term"
    }


def test_condolence_sentence_stays_clear():
    """The hard negative behind dropping `profound`."""
    report = run_checks("We feel a profound sense of loss at Margaret's passing.")
    assert not [f for f in report["must_clear"] if f.get("type") == "flagged_term"]


def test_moved_terms_are_top_level_not_alternatives():
    alternatives = {
        a.lower() if isinstance(a, str) else str(a.get("ai_word", "")).lower()
        for t in load_flagged_terms()
        for a in t["alternatives"]
    }
    for term in [*SHIPPED_TERMS, *DROPPED_TERMS]:
        assert term not in alternatives, term


# ---------------------------------------------------------------------------
# BS-066: the contracted and semicolon negation flip, budget-only
# ---------------------------------------------------------------------------
#
# BS-013 matches only the uncontracted "X is not Y. It is Z." and stays exactly
# as deployed. The contracted and semicolon forms are a separate rule, BS-066,
# and it is budget-only: one flip is ordinary writing (a correction, a
# definition, a disclaimer has the same shape and only semantics separates
# them), so a single instance is never reported and a second flip in one text
# is reported once, as the document_budget overrun with every excerpt.

BS066 = "BS-066"

BS013_POSITIVES = [
    "It's not a tool. It's a partner.",
    "This isn't a bug. It's a feature.",
    "It’s not about the money. It’s about respect.",
    "The issue isn't the budget. It's the timeline.",
    "That's not a strategy. That's a wish.",
    "It wasn't a failure. It was a lesson.",
    "It's not just a product. It's a movement.",
    "The studio is not five machines. It is one path.",
    "It isn't about speed; it's about trust.",
    "This is not a phase. It is a pattern.",
]

BS013_NEGATIVES = [
    "That's not my car. It's my brother's.",
    "It isn't Tuesday. It's Wednesday.",
    "It's not a problem. It's fine.",
    "It's not a ghost. It's the cat.",
    "This isn't the bus stop. It's around the corner.",
    "It's not raining. It's snowing.",
    "That isn't my coffee. It's yours.",
    "The contract is not signed yet. It was sent to them last week.",
    "The build is not ready. It is still running.",
    "It's not 5 p.m. yet. It's half past four.",
]

# The one negative the instance pattern still matches: a misidentification has
# the same construction as the tell. Budget-only makes it moot as one sentence.
GHOST = "It's not a ghost. It's the cat."

# Attested in the wild and deliberately not caught: both end in a bare noun,
# which no regex separates from a bare adjective, weekday or pronoun ("It's
# fine.", "It's Wednesday.", "It's yours."); the bare-noun variant fired on 5 of
# the 10 negatives. Recorded in docs/RULE-HISTORY.md, 2026-11 repair round, BS-066.
ATTESTED_MISSES = [
    "The problem isn't speed; it's trust.",
    "They aren't competitors. They're collaborators.",
]

# Legitimate single uses a narrower pattern spares, one per guard family, from
# the adversarial battery: existential `there` (with an adverb or a line break),
# `let's`, a wh- free relative, `not the only one(s)`, `not one for`, X running
# across a list or heading line, a subordinate first limb, `about` + a number,
# a figure second limb, and dummy-it extraposition.
SPARED_SINGLES = [
    "There really isn't a good answer here. It's a judgment call, and I'd lean toward option B.",
    "Let's not just push the launch again. It's the third slip this quarter, and the client has noticed.",
    "The renewal isn't a big jump. It's about 4% over last year's rate.",
    "Let's not just restart it. It's the third time this week.",
    "There still isn't a fix. It's a known issue upstream.",
    "Write down what's not a priority this sprint. It's a short list.",
    "The PR isn't a big one. It's about 40 lines.",
    "Check who's not a member yet. It's a quick filter in the admin panel.",
    "The Licensee is not an employee of the Licensor. It is the sole responsibility of the Licensee to pay all applicable taxes.",
    "The Contractor is not a fiduciary of the Owner. It is the intention of the parties that this Agreement create no fiduciary duty.",
    "The difference between the groups is not a large one. It is about two percentage points.",
    "Whether the instrument is not a valid one is an empirical question. It is the subject of Section 5.",
    "She wasn't one for speeches. It was a short toast, and then she sat down.",
    "It isn't a long book. It's about 200 pages, and it reads in an afternoon.",
    "The function is not a pure function. It is the caller's responsibility to reset the global state.",
    "If the value is not a string, it is converted with `str()` first. It is a no-op for strings.",
    "The fee isn't 50 dollars. It's 75.",
    "The drive isn't a short one. It's about three hours each way.",
    "The upload limit is not 10 MB. It's 25 MB per file.",
    "Open items:\r\n- The vendor is not a blocker\r\n- Legal review is done.\r\nIt is a good time to schedule the kickoff.\r\n",
    "Notes from Tuesday\r\n- budget is not the issue\r\n- timeline slipped two weeks.\r\nThat's the main risk now.\r\n",
    "### Things that are not a priority\n\nDark mode and i18n. It's a short list for now.",
    "# Release notes\n\n- `parse()` is not a breaking change\n- `load()` returns a dict.\n\nIt is a minor release.",
    "Don't worry, you're not the only one. It's a common mistake.",
    "We weren't the only ones. It was a busy night all over the city.",
    "Thanks for checking. There\r\nisn't a workaround for this. It's a known issue in the vendor SDK.\r\n",
    "There\r\nwas not a sound in the house. It was the middle of the night.\r\n",
]

# Legitimate single uses only semantics separates from the tell: the instance
# pattern matches every one, and budget-only is what keeps each unreported.
INSEPARABLE_SINGLES = [
    "That isn't the invoice. It's the receipt.",
    "The attached file is not the final version. It's a draft for your comments by Friday.",
    "nah it's not a cache issue. it's a DNS thing",
    "The Deposit is not a penalty; it is a genuine pre-estimate of the Landlord's loss.",
    "A p-value is not a measure of effect size. It is the probability of data at least as extreme as those observed, given the null.",
    "The outage was not a cyberattack. It was a faulty software update, the company said.",
    '"This is not a partisan issue. It\'s a safety issue," the senator said.',
    "It wasn't the wind. It was the door to the cellar, banging on its hinge.",
    "This isn't a charge. It's a temporary authorization hold that will drop off in 3 to 5 business days.",
    "The returned slice is not a copy. It is a view into the original buffer, so writes are visible to both.",
    "A whale is not a fish. It's a mammal.",
    "The meeting isn't the 14th. It's the 15th.",
]


# One witness per guard and sub-branch of the BS-066 pattern: a legitimate
# sentence that ONLY that guard spares. Each was checked by deleting the guard
# from a copy of the pattern, after which the witness matches (the mutation
# record is in the 2026-11-12 repair-round task 5 report). Without these, a
# later edit could delete a guard and every other test would stay green.
GUARD_WITNESSES = {
    "there (contracted 's not)": "There's not a cloud in the sky. It's a perfect day for the drive.",
    "there + one space (is not)": "There is not a single seat left. It is a sold-out run.",
    "there + one space (isn't)": "There isn't a train after midnight. It's a long walk home from the station.",
    "there + 2-letter word": "Back there it was not a choice. It was the only road out of the valley.",
    "there + 3-letter word": "There now isn't a fee for that. It's a free service since May.",
    "there + 4-letter word": "There just isn't a good fit for us. It's a niche product.",
    "there + 5-letter word": "There still isn't a fix. It's a known issue upstream.",
    "there + 6-letter word": "There really isn't a good answer here. It's a judgment call, and I'd lean toward option B.",
    "there + 7-letter word": "There usually isn't a queue at this branch. It's a quiet part of town.",
    "there + 8-letter word": "There probably isn't a quick answer. It's a question for legal.",
    "there + 9-letter word": "There certainly wasn't a plan. It was a scramble from the first day.",
    "there + 10-letter word": "There definitely isn't a dress code. It's a casual office.",
    "there + 11-letter word": "There fortunately wasn't a crowd. It was a weekday morning.",
    "there + 12-letter word": "There occasionally isn't a seat on the early train. It's a busy route.",
    "there + line break": "There\r\nwas not a sound in the house. It was the middle of the night.\r\n",
    "let's": "Let's not just restart it. It's the third time this week.",
    "what's": "Write down what's not a priority this sprint. It's a short list.",
    "who's": "Check who's not a member yet. It's a quick filter in the admin panel.",
    "not the only one": "Don't worry, you're not the only one. It's a common mistake.",
    "not the only ones (plural branch)": "We weren't the only ones. It was a busy night all over the city.",
    "not one for": "She wasn't one for speeches. It was a short toast, and then she sat down.",
    "not one to": "He wasn't one to complain. It was a long shift, and he just got on with it.",
    "but inside X": "The delay is not a crisis but a scheduling problem. It is a known issue with the vendor.",
    "struct: blank line": "The vendor is not a blocker\n\nLegal review is done. It is a short list now.",
    "struct: - bullet": "Notes from Tuesday\n- budget is not the issue\n- timeline slipped two weeks.\nThat's the main risk now.",
    "struct: * bullet": "Notes from Tuesday\n* budget is not the issue\n* timeline slipped two weeks.\nThat's the main risk now.",
    "struct: + bullet": "Notes from Tuesday\n+ budget is not the issue\n+ timeline slipped two weeks.\nThat's the main risk now.",
    "struct: > quote": "The budget is not the issue\n> timeline slipped two weeks.\nThat's the main risk now.",
    "struct: # heading": "Why this is not a breaking change\n# Summary of the release.\nIt is a minor version.",
    "struct: | table row": "The id is not a UUID\n| id | integer |.\nIt is a plain column.",
    "struct: numbered list": "Open questions:\n1) Pricing is not a blocker\n2) Legal review is done.\nIt is a short list now.",
    "struct: numbered list (.)": "Open questions:\n1. Pricing is not a blocker\n2. It is a minor issue.\nThat is all.",
    "struct: indented bullet": "Notes from Tuesday\n  - budget is not the issue\n  - timeline slipped two weeks.\nThat's the main risk now.",
    "struct: inner \\r? (CRLF blank line)": "The vendor is not a blocker\r\n\r\nLegal review is done. It is a short list now.",
    "comma clause: it": "If the value is not a string, it is converted with `str()` first. It is a no-op for strings.",
    "comma clause: they": "If the order is not a rush job, they ship it on Monday. It is a standard queue.",
    "comma clause: we": "If the payment is not a refund, we log it as revenue. It is a simple rule.",
    "comma clause: you": "If the file is not a PDF, you can still upload it. It is a supported format.",
    "comma clause: he": "If the patient is not a minor, he signs the form himself. It is a short form.",
    "comma clause: she": "If the tenant is not a student, she pays the full rate. It is a fixed rate.",
    "comma clause: i": "If the bug is not a regression, I leave it for next sprint. It is a judgment call.",
    "comma clause: this": "If the input is not a number, this returns null. It is a common pattern.",
    "comma clause: that": "If the entry is not a duplicate, that row stays. It is a safe default.",
    "comma clause: there": "If the room is not a quiet one, there may be space next door. It is a short walk.",
    "copula+det in X: is": "Whether the instrument is not a valid one is an empirical question. It is the subject of Section 5.",
    "copula+det in X: are": "Rows that are not a match are the ones we drop. They are a small share.",
    "copula+det in X: was": "Anything that was not a donation was a loan. It was a strict household.",
    "copula+det in X: were": "Items that were not a match were the ones we flagged. They were a small batch.",
    "copula+det in X: a": "Whether a ban is not a fair response is a separate question. It is a debate for the board.",
    "copula+det in X: an": "Whether the instrument is not a valid one is an empirical question. It is the subject of Section 5.",
    "copula+det in X: the": "Whether the fee is not a deterrent is the real question. It is the subject of the next section.",
    "about + digit": "The renewal isn't a big jump. It's about 4% over last year's rate.",
    "about half": "The job isn't a big one. It's about half a day of work.",
    "about a dozen (a + quantity)": "The patch isn't a big one. It's about a dozen lines.",
    "about + number word": "The drive isn't a short one. It's about three hours each way.",
    "about the same": "The new plan isn't a big change. It's about the same price as the old one.",
    "about as X as": "The new laptop isn't a big upgrade. It's about as fast as the old one.",
    "digit second limb": "The fee isn't 50 dollars. It's 75.",
    "extraposition: whole guard": "The Licensee is not an employee of the Licensor. It is the sole responsibility of the Licensee to pay all applicable taxes.",
    "extraposition: optional modifier": "The function is not a pure function. It is the caller's responsibility to reset the global state.",
    "extraposition: responsibility": "The function is not a pure function. It is the caller's responsibility to reset the global state.",
    "extraposition: duty": "The landlord is not a party to the claim. It is the duty of the tenant to notify the insurer.",
    "extraposition: obligation": "The bank is not a guarantor of the loan. It is an obligation of the borrower to repay it.",
    "extraposition: intention": "The Contractor is not a fiduciary of the Owner. It is the intention of the parties that this Agreement create no fiduciary duty.",
    "extraposition: condition": "The deposit is not a fee. It is a condition that the keys be returned by noon.",
    "extraposition: requirement": "The interview is not a formality. It is a requirement of the grant that every applicant attend.",
    "extraposition: pleasure": "Our guest is not a stranger to this stage. It is a pleasure to welcome her back.",
    "extraposition: privilege": "The award is not a small one. It is a privilege to accept it on behalf of the team.",
    "extraposition: offence": "Carrying the card is not a requirement. It is an offence to lend it to someone else.",
    "extraposition: offense (US spelling)": "Carrying the card is not a requirement. It is an offense to lend it to someone else.",
    "extraposition: of": "The landlord is not a party to the claim. It is the duty of the tenant to notify the insurer.",
    "extraposition: to": "Our guest is not a stranger to this stage. It is a pleasure to welcome her back.",
    "extraposition: that": "The deposit is not a fee. It is a condition that the keys be returned by noon.",
    "good idea to": "The workshop is not a requirement. It is a good idea to attend, though.",
    "bad time to": "The update is not a security fix. It is a bad time to install it anyway.",
    "great time to": "The weekend is not a holiday here. It is a great time to visit, though.",
    "better practice to": "Logging is not a substitute for tests. It is a better practice to write both.",
    "... idea to": "The workshop is not a requirement. It is a good idea to attend, though.",
    "... time to": "The update is not a security fix. It is a bad time to install it anyway.",
    "... practice to": "Logging is not a substitute for tests. It is a better practice to write both.",
}


@pytest.mark.parametrize("text", list(GUARD_WITNESSES.values()), ids=list(GUARD_WITNESSES))
def test_each_guard_spares_its_witness(text):
    assert not bs066_instances(text)
    assert not bs066_reported(text)


def bs066_instances(text: str) -> list[dict]:
    """The rule's raw instance matches, before budget-only reporting drops them."""
    rules = [s for s in load_regex_structures() if s["id"] == BS066]
    assert rules, "BS-066 is missing from banned_structures.json"
    return find_regex_structures(text, rules)


def bs066_reported(text: str) -> list[dict]:
    return [m for m in run_checks(text, "prose")["must_clear"] if m.get("id") == BS066]


def test_bs066_is_budget_only_with_a_budget_of_one():
    budgets, _ = load_document_budgets()
    assert BS066 in load_budget_only_ids()
    assert budgets[BS066] == 1


def test_bs066_text_says_it_counts_every_form_of_the_flip():
    bs066 = next(s for s in load_json("banned_structures.json")["structures"] if s["id"] == BS066)
    assert "every form" in bs066["description"].lower()
    assert "contracted and semicolon forms" not in bs066["description"]
    assert "real" not in bs066["fix"].split()


def test_bs013_pattern_is_unchanged():
    """BS-013 stays as deployed; the contracted forms are BS-066's job."""
    bs013 = next(s for s in load_regex_structures() if s["id"] == "BS-013")
    assert bs013["detection"]["pattern"] == (
        r"\b(?:is|are|was|were)\s+not\s+(?:just|only|merely|simply|a|an|the|about|one|two"
        r"|three|four|five|six|seven|eight|nine|ten|\d+)\s+[^.?!]{0,45}[.]\s+(?:It|They"
        r"|That|This)\s+(?:is|are|was|were)\b"
    )
    assert "document_budget" not in bs013


@pytest.mark.parametrize("text", BS013_POSITIVES)
def test_single_flip_matches_but_is_not_reported(text):
    """One flip is a matched instance, held back by the budget."""
    assert bs066_instances(text), text
    assert not bs066_reported(text)


@pytest.mark.parametrize("i", range(len(BS013_POSITIVES)))
def test_two_flips_in_one_text_are_the_overrun(i):
    text = f"{BS013_POSITIVES[i]} {BS013_POSITIVES[(i + 1) % len(BS013_POSITIVES)]}"
    hits = bs066_reported(text)
    assert len(hits) == 1, text
    assert hits[0]["type"] == "document_budget" and hits[0]["count"] == 2
    assert len(hits[0]["excerpts"]) == 2


@pytest.mark.parametrize("text", BS013_NEGATIVES)
def test_bs013_negatives_produce_no_overrun(text):
    assert not bs066_reported(text)


@pytest.mark.parametrize("text", [t for t in BS013_NEGATIVES if t != GHOST])
def test_bs013_negatives_are_not_instances(text):
    assert not bs066_instances(text)


def test_ghost_is_an_instance_held_back_by_the_budget():
    """Accepted: the same construction as the tell. One is never reported."""
    assert bs066_instances(GHOST)
    assert not bs066_reported(GHOST)


@pytest.mark.parametrize("text", SPARED_SINGLES)
def test_guarded_legitimate_uses_are_not_instances(text):
    assert not bs066_instances(text)
    assert not bs066_reported(text)


@pytest.mark.parametrize("text", INSEPARABLE_SINGLES)
def test_inseparable_legitimate_singles_are_not_reported(text):
    assert bs066_instances(text), "control: the shape matches; the budget holds it back"
    assert not bs066_reported(text)


@pytest.mark.parametrize("text", ATTESTED_MISSES)
def test_attested_bare_noun_flips_stay_unflagged(text):
    assert not bs066_instances(text)
    assert not bs066_instances(f"{text} {text}")


def test_bs066_meets_the_terse_and_tier1_bar_on_the_overrun():
    def overrun(text: str) -> list[dict]:
        return find_budget_overruns(bs066_instances(text), {BS066: 1}, {}, frozenset({BS066}))

    assert overrun("It's not a tool. It's a partner. This isn't a bug. It's a feature.")
    assert_tier1_clear(overrun, BS066)
    assert_terse_clear(overrun, BS066)
    assert_tier1_clear(bs066_instances, BS066)
    assert_terse_clear(bs066_instances, BS066)


@_NEEDS_TIER2
def test_bs066_is_within_the_tier2_bar_per_instance():
    """Per instance, which bounds the per-document overrun from above."""
    assert tier2_within_bar(tier2_sweep(bs066_instances)[0])


def test_bs066_redos_safe_at_the_cap():
    for text in ("It's not a " * 9100, "It’s not a " * 9100, "is not a" + " " * 100_000,
                 "It's not a tool. It's a partner. " * 3100):
        start = time.perf_counter()
        bs066_instances(text[:100_000])
        assert time.perf_counter() - start < 0.5
