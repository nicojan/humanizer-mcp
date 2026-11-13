"""The served guide must not recommend what its own checker flags.

Every string a writing model reads (the full guide for each content type, plus
the self-review rubric) is walked here. Quoted examples inside guidance fields
either pass the checker or are listed below as deliberate counter-examples (the
bad form the guidance warns against). Anti-pattern "after" texts and lexicon
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
    'It reflects the brief. It reflects the budget. It reflects the deadline.',
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
    'unspoken',
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


def served_texts() -> list[tuple[str, str]]:
    """(JSON path, string) for everything the guide serves, per content type,
    plus the self-review rubric (strings or objects)."""
    texts: list[tuple[str, str]] = []
    for ct in CONTENT_TYPES:
        texts.extend(_walk(build_guide_payload(ct), f"guide[{ct}]"))
    texts.extend(_walk(load_self_review(), "self_review"))
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


def served_quotes() -> list[tuple[str, str]]:
    """(path, quote) for every quoted string inside a guidance field."""
    return [
        (path, quote)
        for path, text in served_texts()
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
    items = load_self_review()
    item = next(i for i in items if "Generic competence" in str(i))
    assert "never invented" in str(item)


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
    assert "not just globally" not in json.dumps(load_json("foundation.json")["section_level_variation"])


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
