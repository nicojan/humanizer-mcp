"""The served guide must not recommend what its own checker flags.

Every string a writing model reads (the full guide for each content type, plus
the self-review rubric's `short` and `detail` texts) is walked here. Quoted
examples inside guidance fields, which include the rubric's `short` and
`detail`, either pass the checker or are listed below as deliberate
counter-examples (the bad form the guidance warns against). The rubric's
`history` is never served and is skipped. Anti-pattern "after" texts and lexicon
alternatives are what the guide tells the model to write, so they must pass.

Later tasks extend this module and reuse its helpers.
"""

import functools
import json
import re
from typing import Any, Iterator

import pytest

from src.checker import run_checks
from src.checker.loader import load_flagged_terms, load_self_review
from src.storage.json_store import load_json
from src.tools.read import build_guide_payload

CONTENT_TYPES: tuple[str, ...] = (
    "academic",
    "marketing",
    "technical",
    "general_prose",
    "creative",
    "case_study",
    "resume",
)

GUIDANCE_FIELDS: tuple[str, ...] = (
    "rewriting_guidance",
    "guidance",
    "notes",
    "human_pattern",
    "human_markers",
    "special_considerations",
    "alternatives",
    "directive",
    "explanation",
    "after",
    "fix",
    "short",
    "detail",
)

# Finding types `fires` reads from must_clear. Length metrics, terminal marks,
# run-ons and comma splices are left out: quoted fragments are not sentences.
_FIRING_MUST_TYPES = frozenset({"banned_structure", "flagged_term"})

# Quotes the guidance shows as the bad form ("AI writes ...", "Instead of ...",
# "X -> Y", "becomes", "not ...", or an `ai_pattern` sentence). Each one fires
# on purpose. A new firing quote fails the quote test until someone decides
# whether it is a counter-example (list it here) or a recommendation (fix it).
COUNTER_EXAMPLES: frozenset[str] = frozenset({
    # anti_patterns.patterns
    'Despite its [positive], [subject] faces challenges...',
    'Eight words to carry',
    "If you've ever struggled with...",
    'In a world where / In an era of',
    "That's where X comes in.",
    'The best part? ...',
    'The key here is...',
    'The kicker? ...',
    'The key is',
    'The point of X is...',
    'The result? ...',
    'The same board, rebuilt.',
    'What changed was X',
    'What matters here is X',
    'When it comes to X, ...',
    "You're not alone",
    "You're not broken",
    "You're not imagining it",
    'at a high level',
    'breathtaking',
    'carries the weight/burden/load',
    'comprehensive',
    'dedicated to showcasing diverse artistic expressions',
    'experts agree',
    'facilitate optimal outcomes',
    'implementation of',
    'in 200 words',
    'in brief',
    'intricate',
    'it is widely believed',
    "it's crucial to remember",
    'leverages',
    'marking a pivotal moment',
    'not just X, but Y',
    'not just X, but also Y',
    'optimization of',
    'optimized',
    'plays a [pivotal/key/central] role in',
    'researchers say',
    'setting the stage for',
    'showcasing',
    'studies show',
    'tapestry',
    'the short version',
    'to put it simply',
    'underscore',
    'underscoring...',
    'vibrant',
    # caveats.core_caveats: attested tells, accepted residuals, and human
    # anaphora that the detector cannot tell apart from the model tell
    'Billiards survives final year.',
    'Busy season eats the Fridays.',
    'Co-op hours were 9 to 5, so the Fridays survived.',
    'Fine. The dog stays.',
    'It does not keep the country free. It does not settle the West. It does not educate.',
    'Method, and why this one',
    'Seven to eight hours of sleep, and I want to keep it there.',
    'The Scouts books and the tutoring stay.',
    'Tutoring stays.',
    'Work does not get to claim them.',
    # content_profile.layer_adjustments
    'Additionally',
    'Furthermore',
    'Furthermore,',
    'Generally speaking...',
    'In conclusion',
    'Innovative,',
    'Moreover',
    'Moreover,',
    'Subsequently...',
    'cutting-edge',
    'cutting-edge,',
    'differentiate',
    'elucidate',
    'facilitate',
    'game-changing',
    'game-changing,',
    'innovative technology',
    'optimize,',
    'seamless',
    'seamless,',
    'streamline,',
    'transformative',
    'utilize the tool',
    # content_profile.special_considerations
    'studies show.',
    # discourse_cohesion.cohesive_devices
    'This approach enables... This enables... This in turn enables...',
    # discourse_cohesion.discourse_markers
    'Additionally,',
    'Furthermore, the team discovered that...',
    # discourse_cohesion.explicit_antithesis_and_reused_shape
    'The studio is not five machines. It is one path.',
    'is rarely X. It is Y',
    # foundation.absolute_rules
    '--',
    ';.',
    # lexical_patterns.flagged_adjectives
    "In today's rapidly evolving",
    'a bustling hub',
    'a vibrant scene',
    'plays a key role in',
    'plays a pivotal role',
    'the tension was palpable',
    'unwavering commitment',
    'nestled',
    # lexical_patterns.flagged_nouns
    'a beacon of hope',
    'a hidden gem',
    'a myriad of',
    'a plethora of',
    'a testament to',
    'a treasure trove of',
    'hidden gem',
    'rich tapestry',
    # lexical_patterns.flagged_verbs
    'Resonate with',
    'This underscores the importance of',
    'bustling',
    'embark on a journey',
    'empower teams to',
    'fostering',
    'nestled in the heart of the valley',
    'unleash the power of',
    'unlock the potential/power of',
    # lexical_patterns.nominalization
    'The implementation of the new policy by the committee',
    'The optimization of the utilization of resources',
    'this serves as a demonstration of',
    # sentiment_tone.readability
    'utilize',
    # sentiment_tone.subjectivity
    'Generally speaking',
    # self_review: the bad forms each rubric item tells the model to read for
    'Billiards survives final year',
    'Busy season eats the Fridays',
    'Elara',
    'It is X, not Y.',
    'It is not a tool. It is a partner.',
    'Work does not get to claim them',
    'eight words to carry',
    'moves the needle',
    'the Fridays survived',
    'the federal purse',
    'the layout carries the weight',
    'the tip of the iceberg',
    # banned_structures fix texts: the bad form each fix quotes so the model can
    # recognise it before rewriting. The recommended forms beside them pass.
    'The point of X is',
    'When it comes to pricing, we keep it simple',
    'Monitoring plays a pivotal role in catching problems',
    "if you've ever felt X",
    'The layout carries the weight of the argument',
    'Quiet confidence',
    'Quietly reshaping the industry',
    'Not because the person stopped mattering, but because the officer is reachable',
    'Each board carries its own title, rule and legend',
    'Slide 18 carries the business model',
    'The margin rail carries the tags',
    'It moves the needle on readiness',
    'The federal purse would feel it',
    "It shipped late, and I'm not going to pretend otherwise.",
    'The report serves as a guide',
    'The building stands as a monument to the era',
    'It represents a shift in how the team works',
    'Not a bug. Not a feature. A fundamental design flaw.',
    # structural_patterns.cross_segment_variation
    'The second draft is the real one.',
    # structural_patterns.syntactic_variety
    'That the system performed well is noteworthy',
    'The policy was updated in March, reflecting a shift in organizational priorities and underscoring the need for ongoing adaptation.',
    'is designed to facilitate',
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _walk(obj: Any, path: str) -> Iterator[tuple[str, str]]:
    """Yield (path, string) for every string under obj, skipping `history`."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if key == "history":
                continue
            yield from _walk(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from _walk(value, f"{path}[{i}]")


def banned_fix_texts(data: dict | None = None) -> list[tuple[str, str]]:
    """(path, text) for every `fix` string in banned_structures.json. These
    ride inside every must_clear finding, so a model reads them as instructions
    even though `build_guide_payload` never carries the layer."""
    structures = (data or load_json("banned_structures.json"))["structures"]
    return [
        (f"banned_structures.structures[{i}].fix", entry["fix"])
        for i, entry in enumerate(structures)
        if isinstance(entry.get("fix"), str)
    ]


def served_texts() -> list[tuple[str, str]]:
    """(JSON path, string) for everything the guide serves, per content type,
    every banned_structures `fix`, plus the `short` and `detail` of every
    self-review rubric item (the parts a report serves; `id`, `applies_to` and
    `history` are not served)."""
    texts: list[tuple[str, str]] = banned_fix_texts()
    for ct in CONTENT_TYPES:
        texts.extend(_walk(build_guide_payload(ct), f"guide[{ct}]"))
    for i, item in enumerate(load_self_review()):
        for field in ("short", "detail"):
            texts.append((f"self_review[{i}].{field}", item[field]))
    return texts


# A straight single quote opens after start, whitespace or an opening bracket
# or punctuation, and closes only when followed by whitespace, punctuation or
# end, so the apostrophes in "Here's" and "don't" are not read as closers.
_CLOSER = r"(?=[\s.,;:!?)\]}/]|$)"
_QUOTE_PATTERNS = (
    re.compile(r'"([^"\n]+)"'),
    re.compile(r"“([^”\n]+)”"),
    re.compile(r"(?:^|(?<=[\s(\[{:;,/—“\"]))‘((?:[^’\n]|’(?=\w))+?)’" + _CLOSER),
    re.compile(r"(?:^|(?<=[\s(\[{:;,/—“\"]))'(?=\S)((?:[^'\n]|'(?=\w))+?)'" + _CLOSER),
)


def _quotes_in(text: str) -> list[str]:
    found: list[str] = []
    for pattern in _QUOTE_PATTERNS:
        found.extend(m.group(1).strip() for m in pattern.finditer(text))
    return [q for q in found if q]


def _in_guidance_field(path: str) -> bool:
    keys = re.findall(r"\.([A-Za-z_]+)", path)
    return any(k in GUIDANCE_FIELDS for k in keys)


def served_quotes(
    texts: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """(path, quote) for every quoted string inside a guidance field."""
    return [
        (path, quote)
        for path, text in (served_texts() if texts is None else texts)
        if _in_guidance_field(path)
        for quote in _quotes_in(text)
    ]


def _finding_id(finding: dict) -> str:
    for key in ("id", "term", "phrase", "rule", "type"):
        if finding.get(key):
            return str(finding[key])
    return "unknown"


# A terminal mark, optionally followed by closing brackets or quotes. A bare
# closing bracket is not terminal, so "But it ships (mostly)" gets a period.
_TERMINAL = re.compile(r"[.!?…][\"'”’)\]]*$")


@functools.lru_cache(maxsize=None)
def _fires_cached(sentence: str) -> tuple[str, ...]:
    report = run_checks(sentence)
    hard = (_finding_id(f) for f in report["hard_violations"])
    must = (
        _finding_id(f)
        for f in report["must_clear"]
        if f.get("type") in _FIRING_MUST_TYPES
    )
    return (*hard, *must)


def as_sentence(text: str) -> str:
    """The sentence `fires` checks: trailing `,;:` trimmed and a period added
    when there is no terminal mark, so a quoted fragment is checked as the
    sentence it would become."""
    sentence = text.strip().rstrip(",;:").strip()
    if sentence and not _TERMINAL.search(sentence):
        return f"{sentence}."
    return sentence


def fires(text: str) -> list[str]:
    """Ids of the hard, banned-structure and flagged-term findings on text,
    checked as `as_sentence(text)`. Results are cached per sentence; the data
    files do not change mid-run."""
    return list(_fires_cached(as_sentence(text)))


# ---------------------------------------------------------------------------
# Helper self-checks (a zero below means nothing unless these fire)
# ---------------------------------------------------------------------------


def test_fires_control_catches_known_tells():
    assert "BS-013" in fires("It is not a tool. It is a partner.")
    assert "pivotal" in fires("This is a pivotal moment")
    assert any(i == "AR-002" for i in fires("One thing — the dash."))
    assert fires("The meeting moved to Thursday.") == []


def test_quote_extraction_handles_apostrophes_and_quote_styles():
    text = (
        "Say 'Here's how we fix it' or \"So\" or “But” or "
        "‘it’s fine’, but don't split users' work."
    )
    assert sorted(_quotes_in(text)) == sorted(
        ["So", "But", "it’s fine", "Here's how we fix it"]
    )


def test_fires_appends_a_period_after_a_closing_bracket(monkeypatch):
    assert as_sentence("But it ships (mostly)") == "But it ships (mostly)."
    assert as_sentence("It ships (mostly).") == "It ships (mostly)."
    assert as_sentence("He said 'done.'") == "He said 'done.'"
    assert as_sentence("Ship it,") == "Ship it."
    # And `fires` checks exactly that sentence.
    seen: list[str] = []
    monkeypatch.setitem(globals(), "_fires_cached", lambda s: seen.append(s) or ())
    fires("But it ships (mostly)")
    assert seen == ["But it ships (mostly)."]


def test_served_quotes_are_found():
    # Pinned below the measured count, so a broken extractor that finds only
    # a fraction fails here.
    assert len({q for _, q in served_quotes()}) > 400


# ---------------------------------------------------------------------------
# Consistency
# ---------------------------------------------------------------------------


def test_every_anti_pattern_after_passes_the_checker():
    for ap in load_json("anti_patterns.json")["patterns"]:
        assert fires(ap["after"]) == [], (ap["id"], fires(ap["after"]))


def test_quoted_guidance_examples_pass_or_are_listed_counter_examples():
    firing = {q for _, q in served_quotes() if fires(q)}
    assert firing <= COUNTER_EXAMPLES, sorted(firing - COUNTER_EXAMPLES)


def test_banned_structure_fix_texts_are_walked():
    paths = [p for p, _ in banned_fix_texts()]
    assert len(paths) > 50
    assert set(paths) <= {p for p, _ in served_texts()}
    assert any(_in_guidance_field(p) for p in paths)


def test_a_firing_quote_planted_in_a_fix_text_fails_the_check():
    planted = {"structures": [{"id": "BS-X", "fix": "Write 'It is not a hammer. It is a partner.' instead."}]}
    texts = banned_fix_texts(planted)
    firing = {q for _, q in served_quotes(texts) if fires(q)}
    assert firing == {"It is not a hammer. It is a partner."}
    assert not firing <= COUNTER_EXAMPLES


def test_counter_example_list_has_no_stale_entries():
    assert COUNTER_EXAMPLES <= {q for _, q in served_quotes()}


def test_alternatives_are_plain_strings_that_pass_the_checker():
    for t in load_flagged_terms():
        for a in t["alternatives"]:
            assert isinstance(a, str), (t["term"], a)
            assert fires(a) == [], (t["term"], a, fires(a))


# ---------------------------------------------------------------------------
# No quotas, no performed traits, no fragment pressure
# ---------------------------------------------------------------------------

REMOVED_PHRASES = (
    "idiomatic expression per section", "The data shows, well, suggests",
    "Actually, it's critical", "better-written than others",
    "may or may not be fulfilled", "low-frequency word per paragraph",
    "at least one 'and' per paragraph", "from at least half",
    "Use fragments for emphasis", "add a short fragment",
    "single punchy sentence", "short punchy sentences", "This reminds me of",
    "fragments for emphasis", "'The gap matters.'",
    "Each student follows one path",
    "the most measurable axis", "undo the burstiness work",
    "trimming changes sentence-length variance",
    "cutting words changes sentence-length variance", "most measurable axis",
    "load-bearing",
    # PR 1 fix wave: removals the spec names that survived in another layer
    "Vary confidence level", "Alternate deliberately",
    "modal/epistemic markers distributed unevenly",
    "these are human transition patterns that AI rarely produces",
    "Which brings up another problem", "Use informal transitions",
    "Occasional omission of non-essential detail", "writing quality is uneven",
    "imperfections introduced by earlier passes", "Increase vocabulary diversity",
    "'vary sentence length' rule",
    # pivot, colon and verdict advice the examples contradicted
    "comma, semicolon, or period", "results are clear:", "'This matters.'",
    # hardening, softening and invented specifics (AR-001)
    "This may not be entirely accurate", "Replace hedging with direct claims",
    "their actual influence varies", "mostly handles edge cases",
    "barely handles edge cases", "formulaic openers that mark no limit",
    "16,000 workers", "feels clunky", "almost no latency",
    "signal an author with actual experience", "Introduce deliberate shifts",
    # rubric items 4 and 8
    "Make one section terse", "Add back the messiness",
    # minor items
    "acceptable in the humanities", "one fragment, one parenthetical aside",
    "'one fragment per paragraph'", "lowest-impact",
    "Drift punctuation use across the document",
    "appear more frequently and unevenly", "a feature, not a bug",
    "restraint, not addition", "The goal is not to make text look unedited",
    "judgment, not prohibition",
    # BS-011 and BS-013 in the guide's own caveat prose
    "the specification, not a defect", "frames, not words",
    "so it is not the length-guessing heuristic",
    # Task 11 sweep: targets, performances and AR-001 contradictions
    "would misfire on real short-form prose", "The numbers don't lie, but they do omit",
    "vary syntactic construction and punctuation", "punctuation choice varies across sections",
    "Use conversational bridges where appropriate", "Reintroduce evaluative language",
    "vary the emotional register", "distribute these unevenly", "Or make a direct claim",
    "at least one needs restructuring", "Distribute adverbs unevenly",
    "the only point in the system", "not 'innovative technology' but",
    # Round 3 (2026-11-13): performed traits, quotas and AR-001 examples
    "occasionally loose reference", "mild looseness", "sometimes loose",
    "Reintroduce sensory", "signal embodied experience", "Reintroduce these",
    "Mix emotional registers", "shorter, sharper sentences", "serious problems",
    "Front-load modifiers occasionally", "Efficiently, the system processes data",
    "Front-load subordinate clauses occasionally", "Vary the order",
    "rewrite at least one", "rephrase at least one", "Vary list lengths",
    "mostly for client presentations", "developing it took most of the time",
    "slightly imperfect", "idiosyncratic word choices", "readers expect personality",
    "surprising choices", "One per paragraph is fine", "Mix word lengths",
    "Mix in plain, short words", "This connects to", "Vary the granularity",
    "Teodora", "takes some patience", "add evaluative commentary",
    "at least one UX decision", "at least one concrete detail",
    # Round 3 fix wave: irregularity targets, ranking examples, invented voice
    "that means use them in some places and not others",
    "must itself be irregular", "should itself be irregular",
    "Professional prose should reflect the writer's judgment",
    "Vary how benefits are presented", "uneven idea development",
    "Allow contradictory emotions", "should saturate the prose",
    "short and sharp in tension", "one particular person with particular preoccupations",
    "most distinctive vocabulary", "followed by a short, confident close",
    "It looks handmade because it is", "of unequal length", "known facts about it",
    "two-item, three-item", "Occasional informal or colloquial words mixed",
    "Occasional topic shifts that feel slightly abrupt",
    "Contractions used in some sentences but not others",
    "reads more human than", "Human writers are uneven here",
    "so the lengths and openings differ", "gives the two paragraphs different lengths",
    "One that lands beats five", "Leave causal links implicit; vary sentence openings",
    "use a plain 'So' or 'But,'", "until no run of three shares one",
    "reliability matters too", "and deployment was the hardest part",
    "Allow personal stance", "AI defaults to objective reporting",
    "Vary paragraph-opening structures", "Pure summary without evaluation",
    "AI tends to present the happy path", "someone who actually uses the product",
    "Instead of 'stakeholder engagement'", "Instead of 'the educational landscape'",
    "Replace generic nouns with specific ones: 'factors' → name the factors;",
)


def test_removed_quota_and_performance_phrases_are_not_served():
    blob = " ".join(s for _, s in served_texts()).lower()
    for phrase in REMOVED_PHRASES:
        assert phrase.lower() not in blob, phrase


def test_served_guidance_sets_no_per_unit_quota():
    quota = re.compile(
        r"\bat least (?:one|two|half)\b[^.]{0,80}\bper (?:paragraph|section|sentence)\b",
        re.I,
    )
    assert [p for p, s in served_texts() if quota.search(s)] == []


_ASKS_FOR_BEATS = (
    re.compile(r"\b(?:add|adding|use|using|include|insert|inserting)\b[^.]{0,20}\bfragments?\b", re.I),
    re.compile(
        r"\b(?:add|adding|use|using|include|insert|inserting)\b[^.]{0,30}\b(?:rhetorical )?questions?\b",
        re.I,
    ),
    re.compile(r"\bshort (?:emphatic|punchy) (?:sentences?|beats?)\b", re.I),
)
# `n't` has no word boundary before it ("don't"), so it sits outside the \b.
_NEGATED = re.compile(r"(?:\b(?:not|never|no)|n['’]t)\s+(?:to\s+)?$", re.I)


def asks_for_beats(text: str) -> bool:
    """True when text asks for a fragment, an inserted question or a short
    emphatic beat. A match right after a negation ("do not add fragments")
    is a prohibition and does not count."""
    for pattern in _ASKS_FOR_BEATS:
        for m in pattern.finditer(text):
            if not _NEGATED.search(text[max(0, m.start() - 16) : m.start()]):
                return True
    return False


def test_asks_for_beats_control():
    assert asks_for_beats("Use rhetorical questions occasionally.")
    assert asks_for_beats("Inserting a rhetorical question breaks the monotone.")
    assert asks_for_beats("Use fragments sparingly.")
    assert asks_for_beats("Rhetorical questions, short emphatic sentences, repetition.")
    assert not asks_for_beats("Do not add fragments or one-line questions for rhythm.")
    assert not asks_for_beats("Keep a question the source asks.")
    assert not asks_for_beats("Don't add fragments.")


def test_no_served_guidance_asks_for_fragments():
    assert [p for p, s in served_texts() if asks_for_beats(s)] == []


def test_arguably_alternatives_keep_the_writer_lean_without_vague_attribution():
    items = load_json("lexical_patterns.json")["flagged_qualifiers"]["items"]
    alts = next(i for i in items if i["ai_phrase"] == "Arguably")["alternatives"]
    for weasel in ("Some would say", "One could argue", "probably", "likely"):
        assert weasel not in alts, weasel
    assert any("if the source names them" in a for a in alts)
    assert "On balance" in alts


# ---------------------------------------------------------------------------
# AR-001 for drafting, the priority order, the framing, the surface targets
# ---------------------------------------------------------------------------


def _ap(ap_id: str) -> dict:
    return next(p for p in load_json("anti_patterns.json")["patterns"] if p["id"] == ap_id)


def test_ar001_covers_drafting_with_placeholders_and_a_fiction_exemption():
    rules = load_json("foundation.json")["absolute_rules"]["rules"]
    d = next(r for r in rules if r["id"] == "AR-001")["directive"].lower()
    for word in ("drafting", "placeholder", "fiction", "invent"):
        assert word in d, word


def test_priority_hierarchy_puts_structure_first_and_texture_last():
    h = load_json("foundation.json")["priority_hierarchy"]
    assert [x["layer"] for x in h] == ["structural_patterns", "discourse_cohesion",
        "sentiment_tone", "content_profile", "lexical_patterns", "psycholinguistic_texture"]
    assert [x["order"] for x in h] == [1, 2, 3, 4, 5, 6]
    lexical = next(x for x in h if x["layer"] == "lexical_patterns")
    assert lexical["impact"] == "hygiene"


def test_surface_statistic_targets_are_not_served():
    g = build_guide_payload("prose")
    assert "pos_distribution_targets" not in g["structural_patterns"]
    assert "function_word_patterns" not in g["lexical_patterns"]
    assert "flesch" not in json.dumps(g["sentiment_tone"]).lower()


def test_core_principle_leads_with_the_repeated_shape():
    e = load_json("foundation.json")["core_principle"]["explanation"].lower()
    assert "sentence length" not in e
    assert "same closer" in e


def test_two_axes_burstiness_is_reported_not_targeted():
    b = load_json("foundation.json")["two_axes"]
    text = json.dumps(b).lower()
    assert "fragment" not in text
    assert "reports" in b["burstiness"]["definition"].lower()
    assert "introducing controlled irregularity" not in text


def test_profiles_keep_source_specifics_rather_than_adding_them():
    blob = json.dumps(load_json("content_profiles.json"))
    assert "Ensure the text includes concrete citations" not in blob
    assert "Include personal anecdotes" not in blob


def test_self_review_specifics_come_from_the_source_or_user():
    item = next(i for i in load_self_review() if i["id"] == "generic_competence")
    assert "never invented" in item["detail"]


def test_ap025_after_adds_no_fact_the_before_lacks():
    after = _ap("AP-025")["after"].lower()
    for added in ("hours", "two years", "deploy day", "dreading", "highest"):
        assert added not in after, added


def test_ap026_after_keeps_the_source_hedges():
    after = _ap("AP-026")["after"]
    assert after.count("can help") >= 2, after
    assert "defence" not in after
    assert "defense" in after


def test_ap021_explanation_describes_the_lengths_plainly():
    assert "15-20" not in _ap("AP-021")["explanation"]


def test_ap032_after_keeps_the_source_claim():
    after = _ap("AP-032")["after"]
    assert "finished design work" not in after
    assert re.search(r"\bdesign\b[^.]*\bis real\b", after), after


ROUTED_TELLS = (
    "is really one thing:",
    "real problems:",
    "real shock",
    "not just sentences within a section",
    "a strong human signal",
    "Replace some neutral descriptions with evaluative ones",
    "Uniform hedging is the problem; a single hedge is ordinary",
    "Cut a qualifier unless the claim has the limit it marks",
    "So is a one-line paragraph placed for impact",
)


def test_routed_tells_are_not_served():
    blob = " ".join(s for _, s in served_texts())
    for phrase in ROUTED_TELLS:
        assert phrase not in blob, phrase


def test_subordination_rule_names_every_relation_its_guidance_lists():
    rule = load_json("discourse_cohesion.json")["subordination_vs_coordination"]["rules"][0]
    for relation in ("causal", "temporal", "conditional", "concessive"):
        assert relation in rule["rule"], relation
        assert relation in rule["guidance"], relation


# ---------------------------------------------------------------------------
# Task 3 fix round 1
# ---------------------------------------------------------------------------


def test_core_principle_opens_with_a_plain_claim_not_a_wh_cleft():
    e = load_json("foundation.json")["core_principle"]["explanation"]
    assert not re.match(r"\s*what\b", e, re.I), e[:60]


def test_qualifier_rule_keeps_the_source_hedges_it_shows():
    """The rule must show a source hedge being kept, and that hedged sentence
    must pass the checker, so the lexicon cannot push a model to drop it."""
    rule = load_json("lexical_patterns.json")["flagged_qualifiers"]["rule"]
    examples = [q for q in _quotes_in(rule) if q.endswith(".") and len(q.split()) > 4]
    assert examples, rule
    flagged = {t["term"].lower() for t in load_flagged_terms()}
    for sentence in examples:
        assert fires(sentence) == [], (sentence, fires(sentence))
        hedges = {"probably", "may", "might", "likely", "appears", "in most"}
        kept = {h for h in hedges if h in sentence.lower()}
        assert kept, sentence
        assert not kept & flagged, kept & flagged


def test_ap028_after_adds_no_fact_and_hardens_nothing():
    ap = _ap("AP-028")
    after = ap["after"]
    assert not re.search(r"\d", after), after
    assert "not a projection" not in after
    assert "Direct claims replace hedged ones" not in ap["explanation"]
    for limit in ("in most cases", "appears"):
        assert limit in after, limit


def test_profile_placeholders_are_scoped_to_drafting():
    for path, text in _walk(load_json("content_profiles.json"), "content_profiles"):
        if "placeholder" in text:
            assert "drafting" in text, path


def test_profiles_set_no_function_word_target():
    assert "function word" not in json.dumps(load_json("content_profiles.json")).lower()


# ---------------------------------------------------------------------------
# Application protocol: every path resolves and every section is visited
# ---------------------------------------------------------------------------

# Foundation's meta-sections describe the protocol itself and are not rules.
# Any other exclusion needs a one-line reason beside it.
PROTOCOL_EXCLUDED = {
    "foundation.application_protocol",
    "foundation.ecosystem_workflow",
    "foundation.primary_usage",
    # Eval-methodology notes for data-file editors; never served.
    "caveats.maintainer_notes",
}

# Data files that are not layers a writing model walks (checker data and the
# rubric the report supplies).
_NON_LAYER_FILES = frozenset({"banned_structures", "self_review"})

_DATA_DIR = "data"


def _protocol_phases() -> list[dict]:
    return load_json("foundation.json")["application_protocol"]["phases"]


def _protocol_paths() -> list[str]:
    return [p for phase in _protocol_phases() for p in phase["rule_paths"]]


def _layer_data() -> dict[str, dict]:
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / _DATA_DIR
    names = sorted(p.stem for p in root.glob("*.json"))
    return {n: load_json(f"{n}.json") for n in names if n not in _NON_LAYER_FILES}


def _path_resolves(path: str, layers: dict[str, dict]) -> bool:
    head, *rest = path.split(".")
    if head == "checker":
        return True
    node: Any = layers.get(head)
    if node is None:
        return False
    for i, seg in enumerate(rest):
        is_list = seg.endswith("[*]")
        key = seg[:-3] if is_list else seg
        if not isinstance(node, dict):
            return False
        if key == "<resolved-type>":
            nxt = next(iter(node.values()), None) if node else None
        elif key in node:
            nxt = node[key]
        elif head == "caveats" and i == 0:
            match = [c for c in node.get("core_caveats", []) if c.get("id") == key]
            if not match:
                return False
            nxt = match[0]
        else:
            return False
        if is_list and not isinstance(nxt, list):
            return False
        node = nxt
    return True


def unresolved_rule_paths() -> list[str]:
    layers = _layer_data()
    return [p for p in _protocol_paths() if not _path_resolves(p, layers)]


def unvisited_sections(
    layers: dict[str, dict] | None = None, paths: list[str] | None = None
) -> set[str]:
    layers = _layer_data() if layers is None else layers
    paths = _protocol_paths() if paths is None else paths
    sections = {
        f"{layer}.{key}"
        for layer, data in layers.items()
        for key in data
        if key != "meta"
    }
    return {s for s in sections if not any(p == s or p.startswith((s + ".", s + "[")) for p in paths)}


def test_every_protocol_rule_path_resolves():
    assert unresolved_rule_paths() == []


def test_every_served_section_is_visited_or_excluded():
    assert unvisited_sections() - PROTOCOL_EXCLUDED == set()


def test_resolver_controls_reject_dead_paths_and_accept_live_ones():
    layers = _layer_data()
    assert not _path_resolves("sentiment_tone.subjectivity_markers", layers)
    assert not _path_resolves("lexical_patterns.flagged_verbs.nope", layers)
    assert _path_resolves("sentiment_tone.subjectivity.rules[*]", layers)
    assert _path_resolves("caveats.uniform_application_paradox", layers)
    assert _path_resolves("content_profiles.profiles.<resolved-type>.layer_adjustments", layers)


def test_protocol_paths_skip_sections_that_were_deleted():
    joined = " ".join(_protocol_paths())
    assert "pos_distribution_targets" not in joined
    assert "function_word_patterns" not in joined


def test_protocol_text_matches_the_priority_hierarchy_and_reported_metrics():
    text = json.dumps(_protocol_phases()).lower()
    assert "highest-impact" not in text
    assert "variance increased" not in text
    assert "not just globally" not in json.dumps(load_json("structural_patterns.json")["cross_segment_variation"])


def test_unvisited_sections_control_reports_an_unlisted_section():
    layers = {**_layer_data(), "lexical_patterns": {"meta": {}, "orphan_section": {}}}
    assert "lexical_patterns.orphan_section" in unvisited_sections(layers, _protocol_paths())
    assert unvisited_sections({"x": {"a": {}}}, ["x.a.rules[*]"]) == set()


def test_layer_data_is_loaded_and_names_the_expected_layers():
    expected = {
        "foundation", "lexical_patterns", "structural_patterns", "sentiment_tone",
        "discourse_cohesion", "psycholinguistic_texture", "content_profiles",
        "anti_patterns", "caveats",
    }
    assert expected <= set(_layer_data())
    assert "banned_structures" not in _layer_data()


_FOLLOWS_A_PHASE = re.compile(r"\bfollow(?:s|ed)?\b[^.]{0,60}\b(?:pass|passes|phase|phases)\b", re.I)


def test_phase_order_control_catches_a_purpose_that_claims_a_different_order():
    claim = "Hygiene work that follows the structural and discourse passes."
    assert _FOLLOWS_A_PHASE.search(claim)
    assert not _FOLLOWS_A_PHASE.search("Sentence length follows the content.")


def test_no_phase_purpose_claims_it_follows_another_phase():
    # Phase order is execution order; priority_hierarchy is an impact ranking.
    for phase in _protocol_phases():
        assert not _FOLLOWS_A_PHASE.search(phase["purpose"]), phase["phase"]


def test_lexical_phase_purpose_states_low_impact_not_a_different_order():
    # Lexical ranks fifth of six in priority_hierarchy (texture is sixth).
    purpose = _protocol_phases()[1]["purpose"]
    assert "a low-impact layer" in purpose
    assert "lowest-impact" not in purpose


# ---------------------------------------------------------------------------
# Fix texts built into the checker (not in the data files)
# ---------------------------------------------------------------------------

_FIX_BATTERY: dict[str, str] = {
    "em_dash": "The plan \u2014 bold \u2014 failed.",
    "stacked_punctuation": "We shipped it,. It worked.",
    "comma_splice": "We shipped the fix, it worked.",
    "missing_terminal_mark": "We shipped the fix on Tuesday and the team was glad",
    "run_on_without_terminal": " ".join(["word"] * 70) + ".",
    "segment_uniformity": "\n\n".join(
        [
            " ".join(["The system processes each incoming record in the queue."] * 4),
            " ".join(["The service handles every pending request in strict order."] * 4),
            " ".join(["The program updates the relevant table after each change."] * 4),
        ]
    ),
    "rule_of_three_density": (
        "We cut cost, time, and risk. The team learned to plan, build, and ship."
    ),
    "credibility_insistence": (
        "A real engagement, mid-build. Each board was detailed and real. "
        "The second draft is the real one. But the design is real. "
        "My first real service-design project. I mapped the real flow. "
        "It runs when a real build has to run in reverse."
    ),
    "document_budget": (
        "The work is judgement, not process. Teams ship early and often. "
        "The answer is restraint, not addition. Reviews stay short. "
        "Design is clarity, not decoration."
    ),
    "BS-009": "This is slow. This costs money. This hurts users.",
    "BS-012": "The implementation of the optimization of the configuration of the system failed.",
    "BS-018": "We tried three layouts and threw two away. The craft is mostly restraint.",
    "BS-020": "AI carries the busywork. It never carries the judgment.",
    "fixed_phrase": "It is worth noting that the team shipped on time.",
}


def _finding_key(finding: dict) -> str:
    if finding.get("type") == "banned_structure":
        return finding["id"]
    return finding.get("type", "")


def _battery_findings() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for text in _FIX_BATTERY.values():
        report = run_checks(text)
        for f in (*report["hard_violations"], *report["must_clear"]):
            out.setdefault(_finding_key(f), []).append(f)
    return out


def test_code_fix_battery_triggers_every_code_level_finding_type():
    """Control: the checks below mean nothing unless each type fired."""
    found = _battery_findings()
    missing = [k for k in _FIX_BATTERY if k not in found]
    assert not missing, missing


def test_code_fix_texts_pass_the_checker():
    """Every code-level fix text is served to the writing model inside the
    check report, so it must pass the checker and must not recommend a colon
    pivot."""
    checked = 0
    for key, findings in _battery_findings().items():
        for f in findings:
            fix = f.get("fix", "")
            if not fix:
                continue
            checked += 1
            assert run_checks(fix)["hard_violations"] == [], (key, fix)
            assert not re.search(r"\bcolons?\b", fix, re.IGNORECASE), (key, fix)
    assert checked >= len(_FIX_BATTERY)


_CODE_FIX_TELLS = re.compile(
    r"\b(?:actually|actual|genuinely|genuine|real|really|quietly|honestly)\b"
    r"|,\s+not\b|\bvary sentence openings\b",
    re.IGNORECASE,
)


def test_code_fix_tell_control():
    from tests.checker.test_rubric import outside_quotes

    assert _CODE_FIX_TELLS.search("End on the concrete thing, not a lesson.")
    assert _CODE_FIX_TELLS.search("The text keeps asserting that the work is real.")
    assert _CODE_FIX_TELLS.search("Leave causal links implicit; vary sentence openings.")
    assert not _CODE_FIX_TELLS.search(outside_quotes("Cut it ('real' x3) and name the thing."))


def test_code_fix_texts_carry_no_tell_words_or_contrast_reflex():
    """The fix strings built into the checker read like the guidance: no
    intensifier, no "X, not Y" and no ask to vary openings for their own sake.
    Quoted tokens (the dominant credibility word) are excluded."""
    from tests.checker.test_rubric import outside_quotes

    bad = [
        (key, f["fix"])
        for key, findings in _battery_findings().items()
        for f in findings
        if f.get("fix") and _CODE_FIX_TELLS.search(outside_quotes(f["fix"]))
    ]
    assert bad == []


# ---------------------------------------------------------------------------
# Sentence-length spread is a reported number, never a finding or a target
# ---------------------------------------------------------------------------

_BURSTINESS_AS_FINDING = re.compile(
    r"burstiness\W+(?:\w+\W+){0,6}?(?:finding|flag|target|trip|check)"
    r"|(?:finding|flag|target|trip|check)\w*\W+(?:\w+\W+){0,6}?burstiness",
    re.IGNORECASE,
)


def test_control_pattern_catches_burstiness_as_a_finding():
    assert _BURSTINESS_AS_FINDING.search("short bullets trip burstiness")
    assert _BURSTINESS_AS_FINDING.search("The burstiness check targets the stdev")
    assert _BURSTINESS_AS_FINDING.search("a single finding, burstiness, at stdev 1.0")
    assert not _BURSTINESS_AS_FINDING.search("High burstiness does not imply authenticity.")


def test_no_served_string_presents_burstiness_as_a_finding_or_target():
    bad = [
        (path, text[:120])
        for path, text in served_texts()
        if _BURSTINESS_AS_FINDING.search(text)
    ]
    assert not bad, bad


# ---------------------------------------------------------------------------
# Served history out, one copy of each directive, the size annotation
# ---------------------------------------------------------------------------

MEASUREMENT = re.compile(
    r"\bper 10k\b|\bTier [12]\b|Gutenberg|tests?/\w|\.py\b|\b20\d\d-\d\d-\d\d\b"
)


def keys_named(obj: Any, names: set[str], path: str = "") -> list[str]:
    """Paths of dict keys in `names`, anywhere in obj."""
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f"{path}.{key}"
            if key in names:
                found.append(here)
            found.extend(keys_named(value, names, here))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            found.extend(keys_named(value, names, f"{path}[{i}]"))
    return found


_CAVEAT_REF = re.compile(r"\bcaveats\.([a-z_]+)")


def caveat_refs_in(texts: list[tuple[str, str]]) -> set[str]:
    """Every id named after `caveats.` in the strings (section names such as
    core_caveats and ethical_considerations are not caveat ids)."""
    sections = {"core_caveats", "ethical_considerations", "maintainer_notes"}
    return {
        m.group(1)
        for _, text in texts
        for m in _CAVEAT_REF.finditer(text)
        if m.group(1) not in sections
    }


def server_with_tools():
    """A fresh server with the read and check tools registered."""
    from mcp.server.fastmcp import FastMCP

    from src.tools.check import register_check_tools
    from src.tools.read import register_read_tools

    server = FastMCP("t")
    register_read_tools(server)
    register_check_tools(server)
    return server


def test_part_a_helper_controls():
    assert keys_named({"a": [{"history": 1}], "b": {"maintainer_notes": []}},
                      {"history", "maintainer_notes"}) == [".a[0].history", ".b.maintainer_notes"]
    assert keys_named({"a": {"b": 1}}, {"history"}) == []
    refs = caveat_refs_in([("x", "see caveats.uniform_application_paradox and caveats.core_caveats")])
    assert refs == {"uniform_application_paradox"}
    for text in ("rates per 10k sentences", "on the Tier 2 corpus", "see tests/checker",
                 "lives in budgets.py", "measured 2026-09-18", "Project Gutenberg"):
        assert MEASUREMENT.search(text), text
    assert not MEASUREMENT.search("Tier-1 prohibitions apply to the whole draft.")


def test_history_keys_are_never_served():
    for ct in CONTENT_TYPES:
        assert not keys_named(build_guide_payload(ct), {"history", "maintainer_notes"}), ct


def test_served_guide_carries_no_measurement_narrative():
    assert [p for p, s in served_texts() if MEASUREMENT.search(s)] == []


def test_every_served_caveat_reference_resolves():
    served_ids = {c["id"] for c in build_guide_payload("prose")["caveats"]["core_caveats"]}
    assert caveat_refs_in(served_texts()) <= served_ids


def test_get_guide_declares_its_result_size():
    import asyncio

    tools = {t.name: t for t in asyncio.run(server_with_tools().list_tools())}
    assert tools["humanizer_get_guide"].meta == {"anthropic/maxResultSizeChars": 80000}


def test_every_page_fits_the_declared_size_and_the_full_guide_does_not():
    """The gate: each page arrives inline in Claude Code, the full guide lands
    in a file. Both sides are measured on the served (compact) JSON."""
    from src.tools.read import GUIDE_PARTS, _compact_json, build_guide_part

    limit = 80000
    for ct in (*CONTENT_TYPES, "not-a-type"):
        for part in GUIDE_PARTS:
            size = len(_compact_json(build_guide_part(ct, part)))
            assert size < limit, (ct, part, size)
        assert len(_compact_json(build_guide_part(ct, None))) > limit, ct


METHODOLOGY_CAVEATS = (
    "rhetorical_figures_defeat_shape_detection",
    "short_corpus_cannot_validate_run_detectors",
    "contrastive_scope_notes_are_the_same_shape",
    "lexicon_rate_is_not_a_detector_rate",
)


def test_methodology_caveats_are_maintainer_notes():
    data = load_json("caveats.json")
    served = {c["id"] for c in data["core_caveats"]}
    notes = {n["id"] for n in data["maintainer_notes"]}
    for cid in METHODOLOGY_CAVEATS:
        assert cid not in served, cid
        assert cid in notes, cid


def test_the_non_uniformity_directive_is_not_restated_in_layer_usage():
    restated = re.compile(r"non-?uniform|\buniform(?:ly)?\b|uniform application|unevenly", re.I)
    for name in ("lexical_patterns", "structural_patterns", "sentiment_tone",
                 "discourse_cohesion", "psycholinguistic_texture", "caveats"):
        usage = build_guide_payload("prose")[name].get("usage", "")
        assert not restated.search(usage), name


def test_section_variation_is_served_once():
    g = build_guide_payload("prose")
    assert "section_level_variation" not in g["foundation"]
    assert "cross_segment_variation" in g["structural_patterns"]


def test_primary_usage_keeps_only_its_statement():
    assert set(build_guide_payload("prose")["foundation"]["primary_usage"]) == {"statement"}


_SINGLE_LAYER_CALLS = (
    ("humanizer_get_summary", {"params": {}}),
    ("humanizer_get_application_protocol", {}),
    ("humanizer_get_foundation", {}),
    ("humanizer_get_lexical_patterns", {"params": {}}),
    ("humanizer_get_structural_patterns", {}),
    ("humanizer_get_anti_patterns", {"params": {}}),
    ("humanizer_get_caveats", {}),
    ("humanizer_get_content_profile", {"params": {}}),
)


def _tool_payload(name: str, args: dict) -> Any:
    import asyncio

    result = asyncio.run(server_with_tools().call_tool(name, args))
    blocks = result[0] if isinstance(result, tuple) else result
    return json.loads(blocks[0].text)


def test_no_tool_serves_history_or_maintainer_notes():
    for name, args in _SINGLE_LAYER_CALLS:
        payload = _tool_payload(name, args)
        assert not keys_named(payload, {"history", "maintainer_notes"}), name


# ---------------------------------------------------------------------------
# Final-review fix wave: served data contradictions
# ---------------------------------------------------------------------------


def test_ar002_directive_does_not_offer_a_colon_as_a_substitute():
    rule = next(r for r in load_json("foundation.json")["absolute_rules"]["rules"] if r["id"] == "AR-002")
    assert not re.search(r"\bcolon\b", rule["directive"].lower())


def test_worksheet_caveat_states_the_confidence_levels_accurately():
    by_id = {s["id"]: s for s in load_json("banned_structures.json")["structures"]}
    assert by_id["BS-053"]["detection"]["confidence"] == "medium"
    caveat = next(c for c in load_json("caveats.json")["core_caveats"] if c["id"] == "worksheet_cells_hide_semantic_tells")
    assert "BS-053 at medium" in caveat["statement"]
    assert "all four" not in caveat["statement"]


def test_credibility_rewrites_carry_no_contrast_reflex_or_insistence_token():
    guidance = load_json("lexical_patterns.json")["credibility_insistence"]["rewriting_guidance"]
    assert not re.search(r"\bnot '[^']+' but\b|\bactually\b", guidance[1])


def test_adverb_list_is_framed_as_keep_and_the_old_key_is_gone():
    adverbs = load_json("lexical_patterns.json")["adverb_patterns"]
    assert "human_adverbs_to_reintroduce" not in adverbs
    assert "human_adverbs_to_reintroduce_notes" not in adverbs
    assert adverbs["human_adverbs_to_keep"]
    notes = adverbs["human_adverbs_to_keep_notes"]
    assert "add none" in notes and "AR-001" in notes
    assert not re.search(r"\bnot to\b|,\s+not\b|rather than", notes)


def test_bs042_fix_recommends_no_form_with_a_fact_absent_from_its_example():
    fix = next(s for s in load_json("banned_structures.json")["structures"] if s["id"] == "BS-042")["fix"]
    example = "It shipped late, and I'm not going to pretend otherwise."
    assert example in fix
    assert set(re.findall(r"\d+|\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b", fix.lower())) == set()
    assert "six weeks" not in fix and "the cause was ours" not in fix
    assert "rather than" not in fix
    assert "states that instead" in fix


def test_bs039_fix_keeps_the_sources_facts():
    fix = next(s for s in load_json("banned_structures.json")["structures"] if s["id"] == "BS-039")["fix"]
    assert "a design" not in fix.lower()


def test_negation_flip_uncontracted_form_fires_bs013():
    assert "BS-013" in fires("It is not a tool. It is a partner.")


def test_anaphora_detail_does_not_leave_the_pronoun_reading_open():
    item = next(i for i in load_self_review() if i["id"] == "anaphora")
    assert "It catches only" not in item["detail"]
    assert "pronoun it" in item["detail"]


def test_strings_changed_in_the_final_wave_carry_no_contrast_shape():
    from src.server import SERVER_INSTRUCTIONS

    caveat = next(c for c in load_json("caveats.json")["core_caveats"] if c["id"] == "worksheet_cells_hide_semantic_tells")
    ar002 = next(r for r in load_json("foundation.json")["absolute_rules"]["rules"] if r["id"] == "AR-002")
    for name, text in (
        ("caveat", caveat["statement"]),
        ("ar002", ar002["directive"]),
        ("server", SERVER_INSTRUCTIONS),
    ):
        assert "rather than" not in text, name
    assert ", and the check-fix" not in SERVER_INSTRUCTIONS


def test_worksheet_caveat_explanation_states_bs053_at_medium():
    caveat = next(
        c for c in load_json("caveats.json")["core_caveats"]
        if c["id"] == "worksheet_cells_hide_semantic_tells"
    )
    assert "BS-053 at 'medium'" in caveat["explanation"]
    assert "BS-052, BS-053, BS-054 and BS-055 (budget-only) cover them at confidence 'low'" not in caveat["explanation"]


def test_design_flaw_rewrites_keep_the_source_strength_and_drop_the_contrast():
    ap = next(p for p in load_json("anti_patterns.json")["patterns"] if p["id"] == "AP-059")
    assert ap["after"] == "This is a fundamental design flaw."
    bs = next(s for s in load_json("banned_structures.json")["structures"] if s["id"] == "BS-046")
    assert "'This is a fundamental design flaw.'" in bs["fix"]
