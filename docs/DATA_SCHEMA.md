# mcp-humanizer: Data Schema

All data files live in `/data/` and are JSON. This document describes their **on-disk** structure (the source of truth). Updates flow via `git push` to this repo plus a container restart on the host; the entrypoint pulls the latest `data/` from GitHub on every container start, after which a tool call sees the new content.

> Schema is documented against the live files. If a field below ever drifts from the actual JSON, the JSON wins; regenerate this doc from the files.

---

## Serving model: what consumers actually receive

Tools do not return raw files. Two transforms apply (`src/tools/read.py`):

- **`_strip_meta`** removes the whole top-level `meta` block, but re-promotes `meta.usage` and `meta.application_rule` (where present) to top-level keys on the served payload.
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

Top-level keys: `meta`, `absolute_rules`, `enforcement`, `core_principle`, `two_axes`, `priority_hierarchy`, `section_level_variation`, `application_protocol`, `ecosystem_workflow`.

| Field | Type | Description |
|---|---|---|
| `absolute_rules` | object | `{description, rules[]}`. The non-negotiable, override-everything directives. |
| `absolute_rules.rules[]` | array of objects | `{id, title, priority, directive}`. Three entries: `AR-001` (preserve meaning), `AR-002` (never use em-dashes), `AR-003` (punctuation must be correct/complete). |
| `enforcement` | object | `{description, zero_tolerance{description, members[]}, non_uniformity_scope, verification}`. The two-tier model: Tier-1 prohibitions (`members[]`) must be eliminated; Tier-2 stylistic moves are the only ones the non-uniformity directive governs. |
| `core_principle` | object | `{statement, explanation, research_basis}`. `statement` is "Do not apply changes uniformly." |
| `two_axes` | object | `{perplexity{definition,low,high,human_tendency}, burstiness{…same…}, summary}`. The two analytical axes. |
| `priority_hierarchy` | array of objects | Six entries `{order, layer, action, impact, risk}`, ordered by `order` (1 = highest impact / lowest risk). |
| `section_level_variation` | object | `{principle, profiles{instructions_or_tutorials, narrative_or_creative, academic_or_technical, opinion_or_argumentation}}`; each profile `{burstiness, perplexity, priority}`. |
| `application_protocol` | object | `{description, uniformity_directive, coverage_invariant, phases[]}`. Served only by `humanizer_get_application_protocol` and inside `get_guide` (not `get_foundation`). |
| `application_protocol.phases[]` | array of objects | Ten entries `{phase, name, purpose, tools[], rule_paths[], stop_condition}`. The ordered traversal that visits every rule path. |
| `ecosystem_workflow` | object | `{pipeline_position, role, call_order, upstream{server,url,role,relationship}, overlap_policy}`. Position relative to `mcp-writer-for-human`. Dropped from `get_guide`'s foundation; kept by `get_foundation`. |

---

## `lexical_patterns.json`

Words, phrases, and constructions that statistical detectors over-associate with AI text. `meta.application_rule` is surfaced to consumers.

Top-level keys: `meta`, `flagged_verbs`, `flagged_adjectives`, `flagged_nouns`, `flagged_transitions`, `flagged_qualifiers`, `function_word_patterns`, `vocabulary_diversity`, `word_length_patterns`, `nominalization`, `abstract_concrete_balance`, `adverb_patterns`, `credibility_insistence`.

| Field | Type | Description |
|---|---|---|
| `flagged_verbs` | array of objects | `{ai_word, alternatives[], severity, notes?, research_basis?}`. `notes` and `research_basis` are optional (`research_basis` is dropped at serve time). |
| `flagged_adjectives` | array of objects | `{ai_word, alternatives[], severity, notes?}`. |
| `flagged_nouns` | array of objects | `{ai_word, alternatives[], severity, notes?}`. |
| `flagged_transitions` | array of objects | `{ai_phrase, alternatives[], severity, notes?}`. Note `ai_phrase` (not `ai_word`). |
| `flagged_qualifiers` | object | `{description, items[]{ai_phrase, alternatives[], severity}, rule}`. Hedging phrases; the `rule` warns against uniform hedging, not individual hedges. |
| `function_word_patterns` | object | `{description, ai_tendencies{overused_in_ai[], underused_in_ai[], notes}, rewriting_guidance[]}`. |
| `vocabulary_diversity` | object | `{description, metrics{ttr, hapax_legomenon_rate, unique_word_count}, rewriting_guidance[]}`. |
| `word_length_patterns` | object | `{description, rewriting_guidance[]}`. |
| `nominalization` | object | `{description, ai_pattern, human_pattern, common_nominalizations[]{nominal, verbal}, rules[]{rule, guidance}, research_basis}`. |
| `abstract_concrete_balance` | object | `{description, ai_pattern, human_pattern, rules[]{rule, guidance}, research_basis}`. |
| `adverb_patterns` | object | `{description, ai_pattern, human_pattern, flagged_ai_adverbs[]{ai_adverb, alternatives[], severity}, human_adverbs_to_reintroduce[], rules[]{rule, guidance}, research_basis}`. |
| `credibility_insistence` | object | `{description, ai_pattern, human_pattern, tokens[], same_token_min, rate_per_words, exclusions[], rewriting_guidance[], research_basis}`. Density config consumed by the `credibility_insistence` checker finding (`src/checker/insistence.py` via `loader.load_credibility_insistence`); fires `must_clear` when a token recurs `same_token_min` times or the set rate exceeds `rate_per_words`. Not severity-bearing, so the `risk_level` filter does not touch it. |

The `risk_level` filter on `humanizer_get_lexical_patterns` filters by `severity` across `flagged_verbs`, `flagged_adjectives`, `flagged_nouns`, `flagged_transitions`, `flagged_qualifiers.items`, and `adverb_patterns.flagged_ai_adverbs`.

---

## `structural_patterns.json`

Sentence- and paragraph-level structural targets (burstiness, syntactic variety, punctuation).

Top-level keys: `meta`, `sentence_length`, `syntactic_variety`, `punctuation_diversity`, `pos_distribution_targets`, `n_gram_patterns`, `enumeration_patterns`, `dependency_proximity`.

| Field | Type | Description |
|---|---|---|
| `sentence_length` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. |
| `syntactic_variety` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}` (11 rules). |
| `punctuation_diversity` | object | `{ai_pattern, human_pattern, rules[]{rule, guidance}}`. First rule restates the AR-002 em-dash ban; remaining rules govern punctuation *drift* among valid options (never correctness; see AR-003). |
| `pos_distribution_targets` | object | `{description, human_tendencies{more_in_human_text[], more_in_ai_text[], notes}, rewriting_guidance[]}`. |
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
| `readability` | object | `{description, ai_pattern, human_pattern, rules[]{rule, guidance}, research_basis}`. |

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
| `profiles` | object | Keyed by content type: `academic`, `marketing`, `technical`, `general_prose`, `creative`. |
| `profiles.<type>.label` | string | Display name (e.g., "Academic and research writing"). |
| `profiles.<type>.description` | string | When this profile applies. |
| `profiles.<type>.perplexity_target` | string | Target perplexity band for this type. |
| `profiles.<type>.burstiness_target` | string | Target burstiness band for this type. |
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
| `patterns[]` | array of objects | 37 entries (`AP-001`…`AP-038`, with gaps). |
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
| `structures[].detection` | object | `{method: phrase\|regex\|heuristic, …}`. `phrase` carries `phrases[]`; `regex` carries `pattern` + `confidence`; `heuristic` carries `confidence`. |
| `structures[].gate` | string | `hard` (blocks `prohibitions_clear`) or `checklist` (surfaced as a must-clear item). |
| `structures[].fix` | string | How to rewrite. |
| `structures[].source_examples` | array of strings | `AP-NNN` ids this was derived from. |
| `structures[].research_basis` | string | Optional provenance for the tell (dropped at serve time by `_drop_keys`). Present on the research-backed discourse entries (`BS-013`…`BS-016`) and the later in-the-wild entries (`BS-017`, `BS-021`, `BS-022`, `BS-023`, `BS-024`, `BS-025`). |

`gate=hard` entries use `method=phrase` only (deterministic, high precision). `gate=checklist` entries surface as located must-clear items in `humanizer_check_text`. The `regex` discourse entries `BS-013` (`negation_flip_antithesis`), `BS-014` (`rarely_flip_aphorism`), `BS-015` (`wh_cleft_pronouncement`), and `BS-016` (`meta_framing_opener`) are all `gate=checklist`, `confidence=low`. Note: two checklist findings are produced by the checker without a `banned_structures` entry: `rule_of_three_density` (clustered three-item lists) and `segment_uniformity` (flat style across ≥3 sections) live in `src/checker/structures.py` and `src/checker/metrics.py` respectively.

The PR2 in-the-wild round (2026-06-28) adds four more entries: `BS-017` (`disclaimer_reversal`) and `BS-019` (`locative_pseudocleft`) are `regex` (auto-wired), while `BS-018` (`copula_maxim_closer`) and `BS-020` (`verb_antithesis_pair`) are `method=heuristic`; their JSON entries are documentary, and the detection logic lives in `src/checker/structures.py` (like `BS-009`/`BS-012`). All four are `gate=checklist`, `confidence=low`. A fifth PR2 finding, `credibility_insistence` (reality-assertion density), is driven by the `lexical_patterns.credibility_insistence` block (see that file), not a `banned_structures` entry. The abstraction-as-agent tell (PR2-#4) is surfaced only as a `manual_review` line plus anti-pattern `AP-033`.

Two later in-the-wild rounds add `regex` entries (both auto-wired via `loader.load_regex_structures`, no code change, so they deploy data-only): `BS-021` (`noun_participle_fragment`, 2026-07-03: the verbless "Noun, past-participle." tell, source `AP-034`) and `BS-022` (`meta_label`, 2026-07-06: a standalone line naming the text's own format or length instead of its subject, source `AP-035`). Both are `gate=checklist`, `confidence=low`. `BS-022` is the mechanizable slice of the "performative framing beat"; its judgment sub-forms (self-satisfied closer, first-person meta-commentary, paradox headline) are a `manual_review` line in `self_review.json`, not a `banned_structures` entry.

The web-research round (2026-07-13, from a survey of current AI-writing tells against existing coverage) adds three more `regex` entries (all auto-wired via `loader.load_regex_structures`, no code change, data-only deploy), all `gate=checklist`: `BS-023` (`validation_reassurance`, source `AP-036`: the fixed second-person reassurance frame "You're not alone." / "It's not just you.", the most-cited *new* 2026 tell; `confidence=medium`), `BS-024` (`vague_authority_attribution`, source `AP-037`: appeals to an unnamed authority "Studies show…" / "Experts agree…", scoped to epistemic-verb frames so named references pass; `confidence=medium`), and `BS-025` (`question_fragment_cadence`, source `AP-038`: the "The best part? It's this." determiner-led NP-fragment question + short answer; `confidence=low`). The same round extends `lexical_patterns.json` with four AI-overused opener transitions (`Additionally`, `Consequently`, `Notably`, `Importantly`) and the promotional/travel-guide register (`bustling`, `breathtaking` adjectives; `hidden gem` noun), and adds one `self_review.json` item (excessive coherence / tidiness). Two candidate tells from the same survey were deliberately **rejected** on evidence: curly/smart-quote detection (a tooling artifact, not an author signal; the eval corpus's own construction notes record human web text as curly and raw AI output as straight, i.e. inverted for this domain) and a bare `quiet` word-flag (an ordinary word; the tell is register/collocation, not the token). Rationale: `caveats.json` `flow_over_surface_features`.

---

## `caveats.json`

Limitations, detector brittleness, ESL sensitivity, and ethics.

Top-level keys: `meta`, `core_caveats`, `ethical_considerations`.

| Field | Type | Description |
|---|---|---|
| `core_caveats[]` | array of objects | 14 entries `{id, statement, explanation}`. Includes `probabilistic_not_deterministic`, `uniform_application_paradox` (the single most load-bearing caveat, also surfaced by `get_summary`), ESL sensitivity, detector brittleness, model-convergence notes, the research-backed `flow_over_surface_features`, `sentence_length_mean_not_a_signal`, and `em_dash_model_specific` (which contextualizes AR-002 without relaxing it), and `performative_framing` (the self-aware flourish is a low-ceiling tell; the device is legitimate in moderation, so it is judgment, not prohibition). |
| `ethical_considerations` | object | `{statement, guidance[]}`. `guidance` is an array of strings. |

## `self_review.json`

The human-likeness self-review rubric: the texture checks the deterministic checker cannot verify, which the **calling model** runs against its own draft (the "human" half of write→check→fix). The server makes no API call; it returns the rubric and the model does the judging in its own turn.

Top-level key: `self_review`.

| Field | Type | Description |
|---|---|---|
| `self_review.description` | string | What the rubric is and how it is consumed (documentary). |
| `self_review.items[]` | array of strings | The rubric lines: AR-001 meaning preservation, rhythm, reused rhetorical shape, section-to-section variation, generic competence/stance, abstraction-as-agent, performative framing beat (self-satisfied closer / first-person meta-commentary / paradox headline), durable-signal note. |

`loader.load_self_review()` returns `self_review.items`, which `run_checks` passes to `assemble_report` as the report's `manual_review` list (sequenced by `next_action`). `assemble_report` keeps a static fallback list, so direct callers without the data layer still get a non-empty `manual_review`. Edit this file and git-push to update; no code change is needed. The abstraction-as-agent item is pinned by `tests/data/test_pr2_additions.py`, and the performative-framing-beat item by `tests/checker/test_self_review.py`.
