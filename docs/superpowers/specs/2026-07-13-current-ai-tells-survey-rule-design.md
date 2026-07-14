# Current AI-writing tells: survey → rule design (2026-07-13)

## Context

A web survey of current (2025-2026) "signs of AI writing" (Wikipedia's
*Signs of AI writing*, Forbes' *15 New Giveaway Signs* (Feb 2026), and
Reddit/blogger/PubMed-era word lists), cross-checked against the checker's
existing coverage (BS-001…BS-022, the lexical lists, `credibility_insistence`,
`rule_of_three_density`, `segment_uniformity`, AR-002 em-dash ban). Goal: find
tells the MCP does **not** address, then add only the ones that survive the
project's false-positive discipline and the `flow_over_surface_features` caveat
(surface word-swaps are low-ceiling; flow/section-variation are durable).

## Added

All `gate=checklist` / `manual_review`, never `hard`. All data-only (regex
entries auto-wire via `loader.load_regex_structures`; lexical entries via
`loader.load_flagged_terms`), so they deploy with a git-push + container
restart, no code change.

| ID | Name | Method | Source | Notes |
|---|---|---|---|---|
| `BS-023` | `validation_reassurance` | regex | `AP-036` | Fixed 2nd-person reassurance frame (`You're not alone.`). The most-cited *new* 2026 tell. Frame-scoped; accepts straight+curly apostrophes. |
| `BS-024` | `vague_authority_attribution` | regex | `AP-037` | Unnamed-authority appeal (`Studies show…`). Scoped to unnamed-agent + epistemic verb; named refs pass. |
| `BS-025` | `question_fragment_cadence` | regex | `AP-038` | `The best part? It's this.` NP-fragment question + answer. Boundary-anchored determiner, ≤3-word NP. |

Lexical (`lexical_patterns.json`): openers `Additionally`, `Consequently`,
`Notably`, `Importantly` (`flagged_transitions`, join the Moreover/Furthermore
family); promotional register `bustling`, `breathtaking` (adjectives),
`hidden gem` (noun). Self-review (`self_review.json`): one item, excessive
coherence / tidiness.

## Rejected (on evidence, not taste)

- **Curly/smart-quote detection.** A *tooling* artifact, not an author signal.
  The eval corpus's own construction note (`eval/corpus/SOURCES.md`) records raw
  **human** web text as curly and raw **AI** output as straight (inverted for
  this MCP's domain), and modern model UIs emit curly quotes regardless. It
  discriminates nothing stable. A measurement against the corpus is null by
  construction (quotes were normalized to ASCII in both piles), and the one
  artifact available points the wrong way. Dropped.
- **A bare `quiet` word-flag.** Reddit-cited as a cross-model crutch, but
  `quiet` is an ordinary word ("a quiet room"); the tell is register/collocation,
  not the token. A word-list flag would be a false-positive magnet: the exact
  low-ceiling trap `caveats.json` `flow_over_surface_features` warns against.
  Left open as a possible future *collocation* detector, not a word flag.
- **Copula-avoidance** (`serves as` / `represents` / `features`) and
  **markup/formatting tells** (Title Case, boldface, emoji bullets) deferred:
  the former is high-FP and only worth a tight heuristic later; the latter is a
  scope-boundary decision (overlaps the designer MCP), not a reflexive add.

## Verification

- 269 tests pass (221 prior + 48 new across the four test files).
- **0/16 structural false positives** on the genuine-human eval corpus
  (`eval/corpus/human`). The lone human lexical hit (`Additionally` in one cover
  letter) is a `moderate` must-clear nudge, identical in class to the existing
  `Moreover`/`Furthermore` entries, by design, not a regression.
- ReDoS-safe: `run_checks` on 200k chars of pathological input ≈ 300 ms; real
  inputs are sub-millisecond. No nested unbounded quantifiers.
- The AI half of the corpus predates these 2026 tells, so it serves as an
  FP-control instrument here, not a recall benchmark.

Tests: `tests/checker/test_validation_reassurance.py`,
`test_vague_attribution.py`, `test_question_fragment.py`,
`test_promotional_lexicon.py`.
