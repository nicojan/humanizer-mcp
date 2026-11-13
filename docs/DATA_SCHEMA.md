# mcp-humanizer: Data Schema

All data files live in `/data/` and are JSON. This document describes their **on-disk** structure (the source of truth). Updates flow via `git push` to this repo plus a container restart on the host; the entrypoint pulls the latest `data/` from GitHub on every container start, after which a tool call sees the new content.

> Schema is documented against the live files. If a field below ever drifts from the actual JSON, the JSON wins; regenerate this doc from the files.

---

## Serving model: what consumers actually receive

Tools do not return raw files. Two transforms apply (`src/tools/read.py`):

- **`_strip_meta`** removes the whole top-level `meta` block, but re-promotes `meta.usage` and `meta.application_rule` (where present) to top-level keys on the served payload. It also drops the keys `research_basis`, `theory`, `history` and `maintainer_notes` at every depth, including at the top level of a layer (`caveats.maintainer_notes` is a top-level key, and the function skips it there as well as in nested values). `notes` is not dropped. A `history` key sits beside the directive it explains (a dated measurement, a rule id, a citation) and a test, `test_no_tool_serves_history_or_maintainer_notes`, walks every tool's payload to confirm none is served.
- **`_drop_keys`** recursively removes `research_basis` and `theory` everywhere (citation/rationale trails for editors; no value to a consuming LLM mid-rewrite). `notes` is **not** dropped: in `content_profiles.json` it is the actionable payload.
- All responses are compact JSON (`separators=(",",":")`).

Per-tool specifics:

| Tool | Serves |
|---|---|
| `humanizer_get_foundation` | `foundation.json` minus `meta` and minus `application_protocol` (the latter has its own tool). Keeps `ecosystem_workflow`. |
| `humanizer_get_guide` | All layer files (meta-stripped) + resolved `content_profile` + a `verification` block. The embedded `foundation` keeps `application_protocol` but drops `ecosystem_workflow`. |
| `humanizer_get_summary` | Curated subset of `foundation`: `absolute_rules`, `enforcement`, `core_principle.statement`, a slim `priority_hierarchy`, a compact `content_profile`, and the `uniform_application_paradox` caveat. |
| `humanizer_get_application_protocol` | `foundation.application_protocol` (read raw; not meta-stripped). |
| `humanizer_get_content_profile` | `profiles` (all) or a single resolved profile. |
| `humanizer_get_anti_patterns` | The bare `patterns[]` array (optionally filtered by `category`). |
| `humanizer_get_lexical_patterns` | `lexical_patterns.json` (meta-stripped), optionally filtered by `severity` via the `risk_level` param. |
| other layer getters | The named file, meta-stripped. |

`severity` / `risk_level` values are `high`, `moderate`, `low` (the API accepts `medium` as a synonym for `moderate`). Content-type values are `academic`, `marketing`, `technical` (alias `tech`), `general_prose` (aliases `prose`, `general`), `creative`; `all` returns every profile. There is no `all` profile object.

Every file carries a top-level `meta` object (stripped before serving). Common `meta` fields: `layer`, `priority`, `description`, `usage`; `lexical_patterns` also has `application_rule`; most layers also have `research_basis`. These are documented once here and omitted from the per-file tables below.

---

## `foundation.json`

Top-level keys: `meta`, `absolute_rules`, `enforcement`, `primary_usage`, `core_principle`, `two_axes`, `priority_hierarchy`, `application_protocol`, `ecosystem_workflow`.

| Field | Type | Description |
|---|---|---|
| `absolute_rules` | object | `{description, rules[]}`. The non-negotiable, override-everything directives. |
| `absolute_rules.rules[]` | array of objects | `{id, title, priority, directive}`. Three entries: `AR-001` (preserve meaning), `AR-002` (never use em-dashes), `AR-003` (punctuation must be correct/complete). |
| `enforcement` | object | `{description, zero_tolerance{description, members[]}, non_uniformity_scope, verification}`. The two-tier model: Tier-1 prohibitions (`members[]`) must be eliminated; Tier-2 stylistic moves are the only ones the non-uniformity directive governs. |
| `core_principle` | object | `{statement, explanation, research_basis}`. `statement` is "Do not apply changes uniformly." |
| `two_axes` | object | `{perplexity{definition,low,high,human_tendency}, burstiness{…same…}, summary}`. The two analytical axes. |
| `priority_hierarchy` | array of objects | Six entries `{order, layer, action, impact, risk}`, ordered by `order` (1 = highest impact / lowest risk). |
| `primary_usage` | object | `{statement, history}`. `statement` is the write, check, fix loop; `history` holds the eval evidence and is never served. |
| (removed) `section_level_variation` | n/a | Removed in PR 2. Its four section types live in `structural_patterns.cross_segment_variation.section_types` as plain descriptions, with no burstiness or perplexity values. |
| `application_protocol` | object | `{description, uniformity_directive, coverage_invariant, phases[]}`. Served only by `humanizer_get_application_protocol` and inside `get_guide` (not `get_foundation`). |
| `application_protocol.phases[]` | array of objects | Ten entries `{phase, name, purpose, tools[], rule_paths[], stop_condition}`. The ordered traversal that visits every rule path. |
| `ecosystem_workflow` | object | `{pipeline_position, role, call_order, upstream{server,url,role,relationship}, overlap_policy}`. Position relative to `mcp-writer-for-human`. Dropped from `get_guide`'s foundation; kept by `get_foundation`. |

---

## `lexical_patterns.json`

Words, phrases, and constructions that statistical detectors over-associate with AI text. `meta.application_rule` is surfaced to consumers.

Top-level keys: `meta`, `flagged_verbs`, `flagged_adjectives`, `flagged_nouns`, `flagged_transitions`, `flagged_qualifiers`, `vocabulary_diversity`, `word_length_patterns`, `nominalization`, `abstract_concrete_balance`, `adverb_patterns`, `credibility_insistence`.

| Field | Type | Description |
|---|---|---|
| `flagged_verbs` | array of objects | `{ai_word, alternatives[], severity, notes?, research_basis?}`. `notes` and `research_basis` are optional (`research_basis` is dropped at serve time). |
| `flagged_adjectives` | array of objects | `{ai_word, alternatives[], severity, notes?}`. |
| `flagged_nouns` | array of objects | `{ai_word, alternatives[], severity, notes?}`. |
| `flagged_transitions` | array of objects | `{ai_phrase, alternatives[], severity, notes?}`. Note `ai_phrase` (not `ai_word`). |
| `flagged_qualifiers` | object | `{description, items[]{ai_phrase, alternatives[], severity}, rule}`. Hedging phrases; the `rule` warns against uniform hedging, not individual hedges. |
| `vocabulary_diversity` | object | `{description, metrics{ttr, hapax_legomenon_rate, unique_word_count}, rewriting_guidance[]}`. |
| `word_length_patterns` | object | `{description, rewriting_guidance[]}`. |
| `nominalization` | object | `{description, ai_pattern, human_pattern, common_nominalizations[]{nominal, verbal}, rules[]{rule, guidance}, research_basis}`. |
| `abstract_concrete_balance` | object | `{description, ai_pattern, human_pattern, rules[]{rule, guidance}, research_basis}`. |
| `adverb_patterns` | object | `{description, ai_pattern, human_pattern, flagged_ai_adverbs[]{ai_adverb, alternatives[], severity}, human_adverbs_to_keep[], rules[]{rule, guidance}, research_basis}`. |
| `credibility_insistence` | object | `{description, ai_pattern, human_pattern, tokens[], same_token_min, rate_per_words, exclusions[], rewriting_guidance[], research_basis}`. Density config consumed by the `credibility_insistence` checker finding (`src/checker/insistence.py` via `loader.load_credibility_insistence`); fires `must_clear` when a token recurs `same_token_min` times or the set rate exceeds `rate_per_words`. Not severity-bearing, so the `risk_level` filter does not touch it. |
| `terms_of_art` | object | `{description, items[]{phrase, protects, field}}`. Added 2026-11-09. Multi-word domain terms that contain a flagged word but have no plainer equivalent ("differentiated instruction"). `loader.load_terms_of_art` feeds the phrases to `find_flagged_terms`, which drops any occurrence of a flagged word that falls inside one, in every content type. Add a term only when every suggested alternative would make the sentence wrong. |

The `risk_level` filter on `humanizer_get_lexical_patterns` filters by `severity` across `flagged_verbs`, `flagged_adjectives`, `flagged_nouns`, `flagged_transitions`, `flagged_qualifiers.items`, and `adverb_patterns.flagged_ai_adverbs`.

**Term entries must be direct elements of their category list.** On 2026-09-17 `nestle`, `renowned`, `diverse array`, `natural beauty` and `profound` were added as `alternatives` of another entry, where no loader reads them, so they never fired. The repair round (2026-11-12) moved four of them to top-level entries (`nestle` in `flagged_verbs`, `renowned` in `flagged_adjectives`, `diverse array` and `natural beauty` in `flagged_nouns`) and dropped `profound` (8.49 per 10k on Tier 2, all legitimate). The test module `tests/checker/test_repair_round_2026_11.py` fails on a term-keyed dict that is nested or misplaced, and on any term in the data that the loader does not return (except the hard-promoted phrases). `alternatives` entries are plain strings, and each must pass the checker.

---

## `structural_patterns.json`

Sentence- and paragraph-level structural targets (burstiness, syntactic variety, punctuation).

Top-level keys: `meta`, `sentence_length`, `syntactic_variety`, `punctuation_diversity`, `n_gram_patterns`, `enumeration_patterns`, `dependency_proximity`.

| Field | Type | Description |
|---|---|---|
| `sentence_length` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `syntactic_variety` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}` (11 rules). |
| `punctuation_diversity` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. First rule restates the AR-002 em-dash ban; remaining rules govern punctuation *drift* among valid options (never correctness; see AR-003). |
| `n_gram_patterns` | object | `{ai_pattern, rewriting_guidance[]}`. |
| `enumeration_patterns` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}, research_basis}`. The rule-of-three / parallel-list tell. |
| `dependency_proximity` | object | `{description, ai_pattern, human_pattern, rules[]{rule, guidance}, research_basis}`. |

---

## `sentiment_tone.json`

Counters the neutral-AI-voice bias and flattened affect.

Top-level keys: `meta`, `neutral_bias`, `emotional_layering`, `subjectivity`, `sensing_and_experience_language`, `readability`.

| Field | Type | Description |
|---|---|---|
| `neutral_bias` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `emotional_layering` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `subjectivity` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `sensing_and_experience_language` | object | `{description, ai_underuses[], rewriting_guidance[]}`. |
| `readability` | object | `{description, ai_pattern, human_pattern, rules[]{rule, guidance}, research_basis}`. The Flesch Reading Ease bands and the Gunning Fog wording were deleted on 2026-11-12: nothing in the checker measures them, and a score target degrades the text. The match-the-reader rule stays. |

All tone changes are constrained by `foundation.absolute_rules` AR-001 (preserve meaning, stance, claims).

---

## `discourse_cohesion.json`

Transitions, discourse markers, cohesive devices, repetition, and clause-combining.

Top-level keys: `meta`, `discourse_markers`, `modal_and_epistemic_markers`, `cohesive_devices`, `repetition_patterns`, `subordination_vs_coordination`.

| Field | Type | Description |
|---|---|---|
| `discourse_markers` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `modal_and_epistemic_markers` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `cohesive_devices` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `repetition_patterns` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `subordination_vs_coordination` | object | `{description, ai_pattern, human_pattern, rules[]{rule, guidance}, research_basis}`. |

---

## `psycholinguistic_texture.json`

The subtlest layer: traces of human cognitive processing. Each sub-object's `theory` field is **dropped at serve time** (`_drop_keys`); consumers receive `human_markers` + `rewriting_guidance`.

Top-level keys: `meta`, `cognitive_load_artifacts`, `self_monitoring_traces`, `lexical_retrieval_signatures`, `discourse_planning_traces`.

| Field | Type | Description |
|---|---|---|
| `cognitive_load_artifacts` | object | `{theory, human_markers[], rewriting_guidance[]}`. |
| `self_monitoring_traces` | object | `{theory, human_markers[], rewriting_guidance[]}`. |
| `lexical_retrieval_signatures` | object | `{theory, human_markers[], rewriting_guidance[]}`. |
| `discourse_planning_traces` | object | `{theory, human_markers[], rewriting_guidance[]}`. |

`human_markers` and `rewriting_guidance` are arrays of strings.

---

## `content_profiles.json`

Per-content-type adjustments that modulate (not replace) the base layers.

Top-level keys: `meta`, `profiles`.

| Field | Type | Description |
|---|---|---|
| `profiles` | object | Keyed by content type: `academic`, `marketing`, `technical`, `general_prose`, `creative`, `case_study` and `resume` (the last two added 2026-11-09). Aliases live in `CONTENT_TYPE_ALIASES` in `src/tools/read.py`. `resume` also changes `humanizer_check_text` (no length or rule-of-three measures, via `RESUME_TYPES` in `src/checker/metrics.py`); every other profile is guidance only. |
| `profiles.<type>.label` | string | Display name (e.g., "Academic and research writing"). |
| `profiles.<type>.description` | string | When this profile applies. |
| `profiles.<type>.perplexity_target` | string | Target perplexity band for this type. |
| `profiles.<type>.burstiness_target` | string | Descriptive band for this type. A data key kept for the schema; no served text presents it as a target, and the checker reports sentence-length numbers only (`metrics.length_mean`, `length_stdev`), never a burstiness finding. |
| `profiles.<type>.layer_adjustments` | object | Keyed by layer (`lexical_patterns`, `structural_patterns`, `sentiment_tone`, `discourse_cohesion`, `psycholinguistic_texture`); each `{aggressiveness, notes}`. **`notes` is the actionable content and is not stripped.** |
| `profiles.<type>.special_considerations` | array of strings | Type-specific reminders. |
| `profiles.creative.research_basis` | string | Present only on `creative` (dropped at serve time). |

Add profiles by editing this file and pushing; there is no runtime write tool.

---

## `anti_patterns.json`

Concrete before/after examples. `meta` carries a `schema` object and an `absolute_rule_compliance` note.

Top-level keys: `meta`, `patterns`.

| Field | Type | Description |
|---|---|---|
| `patterns[]` | array of objects | 68 entries (`AP-001`…`AP-069`, with gaps). |
| `patterns[].id` | string | `AP-NNN`. |
| `patterns[].category` | string | One of: `lexical`, `structural`, `sentiment`, `discourse`, `psycholinguistic`. |
| `patterns[].before` | string | AI-typical version. May intentionally contain anti-patterns (including em-dashes) as the thing being demonstrated. |
| `patterns[].after` | string | Humanized version. MUST conform to `foundation.absolute_rules` (notably AR-002: no em-dashes). |
| `patterns[].explanation` | string | What changed and why. May reference rule IDs from other layers. |

**Absolute-rule compliance.** No `after` string contains an em-dash. Em-dashes appear in this file only inside `before` fields and inside `AP-002` / AR-002 explanations that literally name the character.

---

## `banned_structures.json`

Tier-1 sentence-level AI tells consolidated from `anti_patterns.json` into matchable entries. Consumed by `humanizer_check_text`. Em-dashes are handled directly by AR-002 and not duplicated here.

Top-level keys: `meta`, `structures`.

| Field | Type | Description |
|---|---|---|
| `structures[]` | array of objects | The banned-structure entries. |
| `structures[].id` | string | `BS-NNN`. |
| `structures[].name` | string | Machine name (e.g., `didactic_disclaimer`, `negative_parallelism`). |
| `structures[].description` | string | What the tell is. |
| `structures[].detection` | object | `{method: phrase\|regex\|heuristic, …}`. `phrase` carries `phrases[]`; `regex` carries `pattern` + `confidence`; `heuristic` carries `confidence`. A `regex` pattern is a Python `re` pattern compiled with `re.IGNORECASE`; two entries (`BS-052`, `BS-053`) use Python-only inline-flag syntax (a leading `(?m)`, a scoped `(?-i:...)`) that the browser port translates rather than mirrors verbatim, see `web/README.md`. |
| `structures[].gate` | string | `hard` (blocks `prohibitions_clear`) or `checklist` (surfaced as a must-clear item). |
| `structures[].fix` | string | How to rewrite. |
| `structures[].source_examples` | array of strings | `AP-NNN` ids this was derived from. |
| `structures[].research_basis` | string | Optional provenance for the tell (dropped at serve time by `_drop_keys`). Present on most entries added from 2026-06 onward. |
| `structures[].document_budget` | integer, optional | How many instances of this shape are ordinary in one document before a repeat becomes its own tell (e.g. `1` for `BS-011`, `BS-018`, `BS-038`, `BS-039`, `BS-053`, `BS-055`, `BS-057`). Read by `loader.load_document_budgets` and enforced by `src/checker/budgets.py`, which adds a `document_budget` finding when the count in the text supplied exceeds the budget. The checker only sees the text it is handed, so a section-by-section walk still under-counts; the finding's own text says so. |
| `structures[].budget_only` | boolean, optional | When `true` alongside `document_budget`, single instances of the shape are dropped from the report (they are ordinary writing on their own) and only the budget-overrun finding is reported, carrying every instance's excerpt. Currently `BS-055` (`time_back_refrain`, "get my Fridays back") and `BS-057` (`graded_contrast_about`, "less about X and more about Y"). |

`gate=hard` entries use `method=phrase` only (deterministic, high precision). `gate=checklist` entries surface as located must-clear items in `humanizer_check_text`. The `regex` discourse entries `BS-013` (`negation_flip_antithesis`), `BS-014` (`rarely_flip_aphorism`), `BS-015` (`wh_cleft_pronouncement`), and `BS-016` (`meta_framing_opener`) are all `gate=checklist`, `confidence=low`. Note: two checklist findings are produced by the checker without a `banned_structures` entry: `rule_of_three_density` (clustered three-item lists) and `segment_uniformity` (flat style across ≥3 sections) live in `src/checker/structures.py` and `src/checker/metrics.py` respectively.

The PR2 in-the-wild round (2026-06-28) adds four more entries: `BS-017` (`disclaimer_reversal`) and `BS-019` (`locative_pseudocleft`) are `regex` (auto-wired), while `BS-018` (`copula_maxim_closer`) and `BS-020` (`verb_antithesis_pair`) are `method=heuristic`; their JSON entries are documentary, and the detection logic lives in `src/checker/structures.py` (like `BS-009`/`BS-012`). All four are `gate=checklist`, `confidence=low`. A fifth PR2 finding, `credibility_insistence` (reality-assertion density), is driven by the `lexical_patterns.credibility_insistence` block (see that file), not a `banned_structures` entry. The abstraction-as-agent tell (PR2-#4) is surfaced only as a `manual_review` line plus anti-pattern `AP-033`.

Two later in-the-wild rounds add `regex` entries (both auto-wired via `loader.load_regex_structures`, no code change, so they deploy data-only): `BS-021` (`noun_participle_fragment`, 2026-07-03: the verbless "Noun, past-participle." tell, source `AP-034`) and `BS-022` (`meta_label`, 2026-07-06: a standalone line naming the text's own format or length instead of its subject, source `AP-035`). Both are `gate=checklist`, `confidence=low`. `BS-022` is the mechanizable slice of the "performative framing beat"; its judgment sub-forms (self-satisfied closer, first-person meta-commentary, paradox headline) are a `manual_review` line in `self_review.json`, not a `banned_structures` entry.

The web-research round (2026-07-13, from a survey of current AI-writing tells against existing coverage) adds three more `regex` entries (all auto-wired via `loader.load_regex_structures`, no code change, data-only deploy), all `gate=checklist`: `BS-023` (`validation_reassurance`, source `AP-036`: the fixed second-person reassurance frame "You're not alone." / "It's not just you.", the most-cited *new* 2026 tell; `confidence=medium`), `BS-024` (`vague_authority_attribution`, source `AP-037`: appeals to an unnamed authority "Studies show…" / "Experts agree…", scoped to epistemic-verb frames so named references pass; `confidence=medium`), and `BS-025` (`question_fragment_cadence`, source `AP-038`: the "The best part? It's this." determiner-led NP-fragment question + short answer; `confidence=low`). The same round extends `lexical_patterns.json` with four AI-overused opener transitions (`Additionally`, `Consequently`, `Notably`, `Importantly`) and the promotional/travel-guide register (`bustling`, `breathtaking` adjectives; `hidden gem` noun), and adds one `self_review.json` item (excessive coherence / tidiness). Two candidate tells from the same survey were deliberately **rejected** on evidence: curly/smart-quote detection (a tooling artifact, not an author signal; the eval corpus's own construction notes record human web text as curly and raw AI output as straight, i.e. inverted for this domain) and a bare `quiet` word-flag (an ordinary word; the tell is register/collocation, not the token). Rationale: `caveats.json` `flow_over_surface_features`.

The phrase-frame round (2026-07-25, `docs/proposed-rules-2026-07-25.md`, from a survey of current phrase-frame tells against existing coverage) adds five more `regex` entries (all auto-wired via `loader.load_regex_structures`, no code change, data-only deploy), all `gate=checklist`: `BS-026` (`when_it_comes_to_opener`, source `AP-039`, the "When it comes to X, ..." empty topic preamble; boundary + trailing-comma scoped; `confidence=medium`), `BS-027` (`world_state_opener`, source `AP-040`, "In a world where… / In an era of…" sweeping openers; boundary + fixed determiner-noun skeleton scoped; `confidence=medium`), `BS-028` (`pivotal_role_frame`, source `AP-041`, the "plays a [pivotal/key/central] role in" filler template, restricted to an evaluative-adjective allow-list so neutral "supporting role" passes; `confidence=medium`), `BS-029` (`solution_pivot`, source `AP-042`, the "That's where X comes in." marketing pivot, terminal-scoped so "comes in handy" and locatives pass; `confidence=medium`), and `BS-030` (`empathy_conditional_opener`, source `AP-043`, the "If you've ever struggled with…" manufactured-empathy hook, scoped to an empathy-verb allow-list so anecdotal "If you've ever been to Paris" passes; `confidence=low`). The same round extends `lexical_patterns.json` with the marketing/promotional cluster: verbs (`unlock`, `unleash`, `embark`, `empower`, `elevate`), adjectives (`vibrant`, `invaluable`, `unwavering`, `ever-evolving`), and nouns (`treasure trove`, `plethora`, `myriad`). Verified: 0/16 structural false positives on the genuine-human eval corpus. The corpus predates these 2026 frames, so it validates FP-safety, not recall, recall is covered by the constructed unit tests (`tests/checker/test_phrase_frames_2026_07.py`, `test_lexicon_2026_07.py`). Candidate tells **rejected** on evidence this round: register-dependent openers (`Here's the thing`, `Let's be honest`) as the `flow_over_surface_features` trap, and legitimate high-frequency human discourse markers (`in other words`, `that said`, `to be clear`).

The metaphor-and-2026-tells round (2026-08-06, `docs/proposed-rules-2026-08-06.md`, triggered by an in-the-wild report that metaphorical `carry` is unflagged, plus a survey of tells published since the previous round) adds seven more `regex` entries (auto-wired via `loader.load_regex_structures`, no code change, data-only), all `gate=checklist`: `BS-031` (`metaphorical_carry`, source `AP-044`: the `carries the weight|burden|meaning` collocation plus the text-unit intransitive `eight words to carry`; `load` and `freight` are deliberately excluded because logistics prose uses them literally; `confidence=medium`), `BS-032` (`honestly_fragment_opener`, source `AP-045`: the standalone `Honestly?` candour fragment, anchored as a whole bounded fragment so quoted dialogue passes; `confidence=medium`), `BS-033` (`quiet_prestige_modifier`, source `AP-046`: `quiet confidence` / `quietly reshaping`, allow-listed on both branches so `a quiet room` passes; `confidence=medium`), `BS-034` (`concessive_balance_hedge`, source `AP-047`: `While X has benefits, it also carries risks`, with the hedge verb and its object both allow-listed; `confidence=medium`), `BS-035` (`internal_cross_reference`, source `AP-048`: `As mentioned above` and relatives; `confidence=low`), `BS-036` (`deepening_invitation`, source `AP-049`: `Let that sink in.` and relatives, a fixed phrase set; `confidence=medium`), and `BS-037` (`withheld_insight_teaser`, source `AP-050`: `Here's the kicker` / `the part most people miss`, scoped to the withheld-insight claim so the bare `Here's the thing` marker stays unflagged; `confidence=low`). The same round extends `lexical_patterns.json` with the abstract-prestige metaphor cluster (`mosaic`, `symphony`, `labyrinth`, `beacon`, `bedrock`, `cacophony`, `kaleidoscope`, `odyssey`, `crucible`, `north star`) plus `resonate` and `compelling`, and extends the `self_review.json` abstraction-as-agent item to name metaphorical `carry` as its most frequent instance. Verified: 0/16 structural false positives on the genuine-human eval corpus, ReDoS-safe (133ms on 330k pathological chars), 414 tests green. Candidate tells **rejected** this round: a bare `carry` word-flag (the `flow_over_surface_features` trap; the scoped collocation replaces it), a re-run at `Here's the thing` (the 2026-07-25 rejection stands), and the four Forbes semantic tells (metaphors that almost land, arguments that teleport, missing emotional spikes, too clean to be human) as judgments the server cannot verify, already covered by the `self_review` rubric.

Eight further rounds (2026-08-08 through 2026-09-29) add eighteen more `regex` entries, all `gate=checklist`, all auto-wired via `loader.load_regex_structures` with no code change unless noted: `BS-038` (`appended_wh_label`, source `AP-051`), `BS-039` (`not_but_fragment`, source `AP-052`), `BS-040` (`artifact_subject_carry`, source `AP-053`), `BS-041` (`stale_figure_of_speech`, source `AP-054`), `BS-042` (`conjoined_candour_disclaimer`, source `AP-055`), `BS-043` (`copula_avoidance`, source `AP-056`), `BS-044` (`significance_predicate`, source `AP-057`), `BS-045` (`signposted_conclusion`, source `AP-058`), `BS-046` (`staccato_negation_triple`, source `AP-059`), `BS-047` (`analogy_invitation`, source `AP-060`), `BS-048` (`structure_announcement`, source `AP-061`), `BS-049` (`boasts_feature_brag`), `BS-050` (`elevate_your_x`), `BS-051` (`metaphorical_landscape`), `BS-052` (`time_noun_as_agent`, source `AP-062`), `BS-053` (`clipped_retention_verdict`, source `AP-063`, `document_budget=1`), `BS-054` (`deictic_stance_closer`, source `AP-064`), and `BS-055` (`time_back_refrain`, source `AP-062`, `document_budget=1`, `budget_only=true`). `BS-049`..`BS-051` replace three former bare lexicon entries (`boast`, `elevate`, `landscape`) that were moved out of `lexical_patterns.json` into collocation-scoped structures after each measured a non-trivial false-positive rate on long-form prose as a bare word-flag. `document_budget`/`budgets.py` and the `content_type="label"`/`"notes"` support on `humanizer_check_text` both shipped in this span; full rationale, false-positive guards and rejected candidates for every round: `CLAUDE.md`.

The research round (2026-10-30, `docs/superpowers/specs/2026-10-30-research-round-academic-tells.md`, from a literature survey measured against a default-style Claude sample and two modern human probe sets) adds nine `regex` entries, all `gate=checklist`: `BS-056` (`graded_contrast_like`, `AP-065`, `confidence=medium`), `BS-057` (`graded_contrast_about`, `AP-065`, `confidence=low`, `document_budget=1`, `budget_only=true`), `BS-058` (`chatbot_residue`, `AP-068`, `confidence=high`), `BS-059` (`fiction_stock_phrase`, `AP-067`, `confidence=medium`), `BS-060` (`abstract_emotion_frame`, `AP-067`, `confidence=medium`), `BS-061` (`corrective_framing_disclaimer`, `AP-068`, `confidence=low`), `BS-062` (`optimistic_future_closer`, `AP-066`, `confidence=medium`), `BS-063` (`importance_flag`, `AP-066`, `confidence=low`) and `BS-064` (`as_much_about_aphorism`, `AP-066`, `confidence=low`), and extends `BS-030` with the 'If this sounds familiar, take heart' opener. `BS-062` is scoped to the final paragraph by a trailing lookahead that refuses any later paragraph break. None of the round's patterns uses a scoped inline flag group, so the browser port translates them directly. Lexicon: `camaraderie` and `unease` in `flagged_nouns`, `palpable` and `unspoken` in `flagged_adjectives`, all `severity=low`. Corrections in the same round: `vocabulary_diversity` no longer claims human text has the higher type-token ratio, the passive-voice guidance in `structural_patterns` no longer claims AI uses the passive more, and `human_adverbs_to_keep` (named `human_adverbs_to_reintroduce` until the repair round) drops `quietly`, `actually` and `honestly`, with the reason in the new `human_adverbs_to_keep_notes` string. Data only, so a **restart** deploys it.

---

The repair round (2026-11-12) adds one `regex` entry, `BS-066` (`contracted_negation_flip`, `AP-029`), `gate=checklist`, `confidence=low`, `document_budget` 1, **`budget_only` true**: a single instance is never reported and two or more in one text are reported as the overrun with every excerpt attached. It counts every form of the "It's not X. It's Y." flip toward one budget, contracted or not, with a straight or curly apostrophe, closed by a period or a semicolon, behind eleven guards. `BS-013` is deliberately unchanged, because widening it per instance fired on 169 of 217 constructed modern items, 101 of them legitimate. `BS-065` is skipped (named by the rejected caption draft in `tests/support/test_terse_register.py`). Known misses ("The problem isn't speed; it's trust.", where the second half ends in a bare noun) are pinned unflagged in `tests/checker/test_repair_round_2026_11.py`. Auto-wired by `loader.load_regex_structures`, so data-only.

## `caveats.json`

Limitations, detector brittleness, ESL sensitivity, and ethics.

Top-level keys: `meta`, `core_caveats`, `ethical_considerations`, `maintainer_notes` (never served).

| Field | Type | Description |
|---|---|---|
| `core_caveats[]` | array of objects | 21 entries `{id, statement, explanation, history?}`; `history` holds the dated measurement behind a caveat and is never served. Four eval-methodology caveats (`rhetorical_figures_defeat_shape_detection`, `short_corpus_cannot_validate_run_detectors`, `contrastive_scope_notes_are_the_same_shape`, `lexicon_rate_is_not_a_detector_rate`) and the history halves of `labels_are_where_the_tells_hide` and `worksheet_cells_hide_semantic_tells` moved to the top-level `maintainer_notes[]`, which `_strip_meta` drops. The list below predates that move. Includes `probabilistic_not_deterministic`, `uniform_application_paradox` (the caveat most often cited, also surfaced by `get_summary`), ESL sensitivity, detector brittleness, model-convergence notes, the research-backed `flow_over_surface_features`, `sentence_length_mean_not_a_signal`, and `em_dash_model_specific` (which contextualizes AR-002 without relaxing it), `performative_framing` (the self-aware flourish is a low-ceiling tell; the device is legitimate in moderation, so it is a self_review judgment item and stays out of the hard prohibitions), and `metrics_do_not_apply_to_label_text` (the sentence-length numbers and `segment_uniformity` are undefined on headings and fragments, and the prose-shaped structural coverage misses label-register tells; documented rather than detected, because guessing "this input is labels" would misfire on ordinary short-form prose), `labels_are_where_the_tells_hide`, `jargon_substitution_loses_meaning` (Orwell rule 5 has a carve-out: define a domain term at first use, then use it, and never swap it for a vaguer everyday word, which would change the claim), `per_section_checks_miss_document_budgets` (the one-per-piece budgets cannot be enforced from per-section calls, because the checker is stateless and each call sees one instance; the last run must be on the assembled document), `rhetorical_figures_defeat_shape_detection` (a deliberate rhetorical figure and its abusive twin are the same construction, so no shape detector separates them; measured on anaphora at 0/15 precision, and a parser would not help), and `short_corpus_cannot_validate_run_detectors` (`eval/corpus/human` averages under seven sentences per file, so a 0/16 pass from it is not evidence for any run-length or cross-sentence rule).; and `worksheet_cells_hide_semantic_tells` (2026-09-29: a B2 worksheet exemplar passed clean with six reviewer-flagged phrases; records BS-052..BS-055, their recall, and that three of the four have blind corpus zeros and ship at `confidence=low`); and `default_model_prose_mostly_passes` (2026-10-30: 21 of 32 default-style Claude pieces passed with two findings or fewer, and the two strongest published stylometric effects did not transfer to them); and `reviewed_copy_passes_the_checker` (2026-11-09: all 31 lines a reviewer flagged as AI-coded in a month of portfolio copy had passed, and no regex rule could catch them without flagging terse ordinary writing) |
| `ethical_considerations` | object | `{statement, guidance[]}`. `guidance` is an array of strings. |

## `self_review.json`

The human-likeness self-review rubric: the texture checks the deterministic checker cannot verify, which the **calling model** runs against its own draft (the "human" half of write→check→fix). The server makes no API call; it returns the rubric and the model does the judging in its own turn.

Top-level key: `self_review`.

| Field | Type | Description |
|---|---|---|
| `self_review.description` | string | What the rubric is and how it is consumed (documentary). |
| `self_review.items[]` | array of objects | One object per rubric item: `id` (snake_case), `short` (one actionable line, at most 200 characters, served by default), `detail` (the full item, served with `rubric="full"`), `applies_to` (`["all"]` or canonical content types from `src/content_types.py`) and optional `history` (maintainer notes such as measurements, dates and rule ids; never served). Items: meaning preservation (AR-001), rhythm, reused rhetorical shape, the contrastive 'X, not Y' and negation-flip item, section-to-section variation, generic competence/stance, abstraction-as-agent, performative framing beat, excessive coherence, appended significance label, the plainness pass, durable signal, anaphora, over-explained subtext, reader contact (`general_prose`, `marketing`, `case_study`), recognisable defaults, and the portfolio items `so_tail`, `backstory_and_self_portrait` and `cold_reader_test` (`case_study`, `resume`, `marketing`). `rhythm` and `section_variation` skip `label` and `resume`. |

`loader.load_self_review()` is the runtime loader and it degrades instead of failing a check. A legacy string item (a new image on an old data volume) is served as an object whose `short` and `detail` are the string, whose `applies_to` is `["all"]` and whose `id` is `legacy_` plus the first eight hex digits of the string's SHA-1; any other malformed item is skipped with a logged warning. `loader.load_self_review_strict()` is the validator the data tests call, and it raises `ValueError` on a legacy string or a malformed item, so CI still fails on bad data. A file whose container is not a `self_review` object holding an `items` list is an error, never an empty rubric. `loader.check_self_review_at_startup()` runs once when the server starts, never raises, and logs how many items will be served, a warning when legacy string items were mapped (the data volume may be stale), and an error when the container is broken (Python `logging` on stderr; the per-request access log on stdout is a separate stream). `so_tail`, `backstory_and_self_portrait` and `cold_reader_test` list `label` in `applies_to` beside `case_study`, `resume` and `marketing`, so label copy keeps the portfolio items; `reader_contact`, `rhythm` and `section_variation` stay off it. `checker.rubric.rubric_lines(content_type, mode)` filters them by canonical content type (a missing or unknown type gets every item) and returns each item's `short` (mode `"short"`, the default) or `detail` (mode `"full"`); `run_checks` passes that list to `assemble_report` as the report's `manual_review` (sequenced by `next_action`). `assemble_report` keeps a three-line generic fallback, so direct callers without the data layer still get a non-empty `manual_review`. Edit this file and git-push to update: no code change needed. The abstraction-as-agent item is pinned by `tests/data/test_pr2_additions.py`, and the performative-framing-beat item by `tests/checker/test_self_review.py`.
---

## `tests/data/test_guide_consistency.py`: the served guidance obeys the checker

Not a data file, but it constrains every one of them (added 2026-11-12). It builds the served payload for all seven content profiles (`build_guide_payload`) plus the self-review rubric, walks every string in the guidance fields (a `history` key is skipped), and extracts every quoted example. Each quote offered as a recommendation or a rewrite must not fire a hard violation, a `banned_structure` finding or a `flagged_term` finding; a quote that is a deliberate counter-example goes in `COUNTER_EXAMPLES`, under a comment that names the section it comes from. Every string `alternatives` entry in `lexical_patterns.json` must pass the same way. The module also pins the removed quotas and performed-trait phrases (`REMOVED_PHRASES`), checks that every path in `foundation.application_protocol` resolves to a section that exists and that every layer section is visited or deliberately excluded (`application_protocol`, `ecosystem_workflow`, `primary_usage`), and asserts that the burstiness wording is gone from every served file. The quote, alternative, path and section checks each have a control that fails on known-bad input, so a green run there is not a blind zero. The `REMOVED_PHRASES`, `ROUTED_TELLS` and quota checks are absence tests with no control of their own. A companion module, `tests/data/test_guide_pr1_fix_wave.py`, pins the guidance that the review's fix wave kept but conditioned on the source (`AR-001`), the rewritten anti-pattern afters, and a guard against em-dashes in served prose outside `before` fields and the form that names the character, whose control fires on a planted dash. Adding guidance with an example the checker flags fails here, not in a user's draft.
