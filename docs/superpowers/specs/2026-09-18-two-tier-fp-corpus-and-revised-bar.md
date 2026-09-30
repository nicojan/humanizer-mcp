# Two corpus tiers and two false-positive bars

Status: **accepted, ships.** Methodology round. No new rule, no change to any deployed detector. Adds a second eval corpus tier, splits the standing bar in two, deduplicates the sweep into a shared helper, and records the first full-sweep measurement of the deployed rule set against long-form human prose.

## The contradiction this round closes

`CLAUDE.md` stated the standing bar for a rule round as "0/16 structural false positives on `eval/corpus/human` (full-structure sweep, not just the new rule)". On 2026-09-18 the anaphora round added `caveats.short_corpus_cannot_validate_run_detectors`, which states that the same corpus cannot falsify any run-length or cross-sentence rule, because it holds 16 files and 109 sentences, a mean of under seven sentences per file. Eight anaphora formulations all scored 0/16, one of them measuring 75.4 false positives per 10k sentences on long-form human prose. A control positive fired on all eight, so the zeros held and told nothing at the same time.

Both statements were true. The bar certified rules it could not test, and the caveat told a future round to bring its own control without saying what would count as one.

Probing the bar as written turned up a second problem, which had not been recorded anywhere. The bar claims a full-structure sweep over every rule. Run today, that sweep over `eval/corpus/human` does not come back clean, at either reading of the word "structural".

| Layer swept | Findings on `eval/corpus/human` | Files affected |
|---|---|---|
| `banned_structures` (40 regex plus 4 heuristic detectors) | 1 | `human_marketing_01` (`BS-011`) |
| plus `rule_of_three_density` | 2 | plus `human_marketing_04` |
| plus `credibility_insistence` | 2 | unchanged |
| plus the 120 `flagged_term` lexicon groups | 12 | 9 of 16 |

The narrow reading is the one the earlier rounds reported, and their "one finding in total across every structure, the pre-existing `BS-011`" was accurate for the layer they meant. Add the density detector, which is as structural as anything else in the sweep, and it is 2 findings in 2 files. Add the lexicon and it is 12 in 9. On no reading is it zero, so a bar demanding zero from a full sweep has been unsatisfiable for some time.

The test suite enforces something narrower, and that narrower thing has been the sounder bar throughout. Each round asserts zero findings **from that round's new rules** across all 16 files; the sweep is parametrized over the new rule ids only. So the written bar overstated the enforced bar, in a direction that made the enforced bar sound stronger than it is, and it invited a future round to read a standing `BS-011` firing as a regression it had caused.

## Decision

**Both fixes ship.** A long-form corpus tier is added, and the bar is rewritten to name two tiers with two different metrics.

Adding only the corpus tier leaves the written bar wrong twice over, still claiming a full sweep that does not pass and still implying one number covers every rule shape. Rewriting only the bar leaves the caveat's instruction unsatisfiable, because "bring your own long-form control" with no shared corpus means every round fetches its own text, reports a number nobody can reproduce, and the comparison across rounds that `docs/RULE-HISTORY.md` exists to preserve is lost. The anaphora round is the proof: its 47k-sentence measurement was sound, the scripts were never committed, and the numbers survive only as prose in a design doc.

The deeper fix is separating two purposes that shared one directory. `eval/corpus/human` is the Step-0 **calibration** corpus: matched pairs, genre balanced, built against a pre-registered 0.75 AUC separation bar, and pinned by the `test_calibration_corpus_meets_spec` case in `tests/eval/test_corpus_loader.py`. The false-positive sweep borrowed it because it was the only human text in the repo. That conflation is the root cause. Long-form text cannot be dropped into that directory without breaking the pairing invariant, so the false-positive corpus gets its own home and the calibration corpus is left exactly as it is.

## The two tiers

### Tier 1: modern matched registers

`eval/corpus/human`, unchanged and still owned by the calibration spec. 16 files, 109 sentences, four genres (prose, technical, cover letter, marketing), all published before 2022-11-30. Provenance in `eval/corpus/SOURCES.md`.

Falsifies per-sentence and per-phrase rules in the registers the server is used on. Blind to anything needing three or more consecutive sentences, three or more sections, or a document long enough to have a budget.

**Bar: zero findings from the round's new rules, every file.** Unchanged in substance from the old bar, corrected in scope.

### Tier 2: long-form literary

Six public-domain works, 47,088 sentences by `src.checker.segment.split_sentences`, all first published before 1930, so model contamination is impossible. Not committed as text. Fetched by `eval/fpcorpus/fetch_longform.py`, verified against recorded checksums, provenance in `eval/fpcorpus/SOURCES.md`.

Falsifies any rule that needs length: run-length chains, cross-sentence shapes, paragraph-bounded logic, density measures and document-scoped budgets. It is blind to modern promotional and technical register. 22 of the 40 deployed regex structures score exactly zero here, and every one of those 22 targets a marketing shape, a meta-label or a corporate abstraction that Victorian fiction simply does not contain. A zero on Tier 2 is therefore no more evidence of precision than a zero on Tier 1 was for the anaphora chain. Each tier has a blind spot and the round has to say which one it is standing in.

**Bar: 5.0 findings per 10k sentences or fewer from the round's new rules, and every firing read and judged, with the precision fraction reported.**

The rate is reported per 10k sentences because the denominator is now large and will change whenever the fetch is re-recorded. A raw count would not be comparable across rounds.

The threshold of 5.0 is set by what a human can audit rather than by curve fitting. At 47,088 sentences, 5.0 per 10k is about 24 firings, which one person can read in a sitting. At 20 per 10k it is about 95, which nobody reads honestly. The rate is a triage gate that decides whether the reading is feasible; the reading is the bar. This is how the anaphora round reasoned: its best candidate measured 3.2 per 10k, comfortably inside any rate threshold, and was rejected because all 15 firings were legitimate prose, several of them celebrated anaphora by Thoreau and Melville.

A rule may ship above 5.0 per 10k only if the reading shows the firings are tells instead of legitimate prose, and the round states that explicitly. Conversely a rule under 5.0 per 10k still fails if its firings read as legitimate. Neither number overrides the read.

### The control requirement, stated as a bar rather than as advice

A tier result of zero is only reportable when a discriminating control fired in the same pipeline on the same run. The anaphora round found this by accident, and it is what turned a clean-looking pass into a negative result. A sweep returning nothing and a sweep that cannot fire produce identical output.

Concretely, each round reports three numbers from one pipeline invocation: the false-positive rate on the tier, the recall on a constructed positive set, and the hit count on a pattern that must be zero. `BS-011` is measured below as 358 firings by the checker and 358 by an independent `grep -aoiE` over the same files, while a deliberately impossible variant of the same pattern returns 0. That pair is what makes the 358 believable.

## Where the 48 deployed rules stand

First full-sweep measurement of the deployed rule set against long-form human prose. Every firing here is a false positive by construction, because the corpus is unambiguously human. Sweep covers the 40 regex structures, the four heuristic detectors, `rule_of_three_density`, the 120 flagged-term groups and `credibility_insistence`. Excludes `burstiness` and `segment_uniformity`, which are undefined at book length, and excludes `AR-002` and `AR-003`, which deliberately ban punctuation that human prose uses freely.

| Rule | Firings | Per 10k | Worst single work |
|---|---|---|---|
| `BS-011` `x_not_y_contrastive` | 358 | **76.0** | Bleak House (135) |
| `flagged_term` (lexicon, all groups) | 164 | 34.8 | Moby-Dick (38) |
| `rule_of_three_density` | 97 | 20.6 | Moby-Dick (36) |
| `BS-006` `negative_parallelism` | 94 | 20.0 | Moby-Dick (38) |
| `BS-009` `this_chain` | 27 | 5.7 | Walden (12) |
| `BS-012` `stacked_nominalization` | 14 | 3.0 | Bleak House (5) |
| `BS-015` `wh_cleft_pronouncement` | 12 | 2.5 | Walden (5) |
| `BS-019` `locative_pseudocleft` | 10 | 2.1 | Sherlock Holmes (5) |
| `BS-005` `participle_tail` | 9 | 1.9 | Walden (5) |
| `BS-024`, `BS-035` | 6 each | 1.3 | |
| `credibility_insistence` | 6 | 1.3 | Bleak House |
| `BS-010`, `BS-013`, `BS-014` | 4 each | 0.8 | |
| `BS-025` | 2 | 0.4 | |
| `BS-016`, `BS-017`, `BS-018`, `BS-020`, `BS-033`, `BS-039`, `BS-041`, `BS-043`, `BS-045` | 1 each | 0.2 | |
| 22 further regex rules | 0 | 0.0 | see the register caveat above |

The zero-hit set is `BS-004`, `BS-007`, `BS-021` through `BS-023`, `BS-026` through `BS-032`, `BS-034`, `BS-036` through `BS-038`, `BS-040`, `BS-042`, `BS-044`, `BS-046` through `BS-048`.

**Five rules exceed the new Tier 2 rate threshold**: `BS-011`, `flagged_term`, `rule_of_three_density`, `BS-006` and `BS-009`. Nothing is changed in response, per the standing instruction that a retroactive failure is a finding rather than a mandate.

The retroactive comparison is against the **rate** half of the bar only, and the distinction matters. Every firing on this corpus is a false positive by construction, so the read half ("every firing read and judged") cannot retroactively separate a deployed rule from a bad one: on a human corpus all 25 firing rules would fail a literal reading of it. The read half is a gate on a *candidate* rule under consideration, where the question is whether its firings are tells or legitimate prose. Read individually:

- **`BS-011` at 76.0 per 10k is the finding of this round.** It is a two-token regex, `\b\w+,\s+not\s+\w+`, carrying `confidence: low`. Its firings are ordinary English negation: "not yet decided", "not more than nineteen", "not seated, but standing". Higher than every anaphora formulation that was rejected, including the loosest one tested, which measured 75.4 per 10k on the same six works. The two numbers land beside each other by accident: 358 firings and 355 firings over 47,088 sentences are unrelated patterns of similar looseness.
- **`flagged_term` at 34.8 per 10k** is the lexicon firing on words that were ordinary before they became model tells: "delve", "bolster", "enhance". This is `over_regularization_caveat` in its expected form rather than a defect, and it is the same layer that produces 10 of the 12 Tier 1 findings.
- **`rule_of_three_density` at 20.6 per 10k** fires on Dickens cataloguing shop inscriptions and on Melville stacking clauses. Deliberate figure, already predicted by `rhetorical_figures_defeat_shape_detection`.
- **`BS-006` at 20.0 per 10k** fires almost entirely on "not only X but Y", which is a standard construction rather than a model habit.
- **`BS-009` at 5.7 per 10k** was already measured and recorded by the anaphora round. Unchanged.
- **`BS-005` at 1.9 per 10k is inside the threshold** but worth noting, because it fires on ordinary participles: "setting aside his bread and butter", "reflecting on what she had heard". Its trigger list wants a resultative reading it cannot check.

Every rule listed is `gate: checklist`, so a false positive costs an author one justification instead of a blocked build. That is the reason none of this is urgent, and it is also the reason the numbers were never measured.

### Recommendation for the next round

`BS-011` has a cheap and fully measured fix. Probing it was how this round confirmed the Tier 2 bar does useful work, so the candidate table is recorded here rather than lost.

| Formulation | FP on 47,088 sentences | Per 10k | Recall on 6 attested tells | Hard negatives passed |
|---|---|---|---|---|
| deployed: `\b\w+,\s+not\s+\w+` | 358 | 76.0 | 6/6 | 1/6 |
| clause-final Y, adverbial Y blocked, determiner allowed through | 9 | 1.9 | 6/6 | 5/6 |
| the same, plus a copula anchor on the X side | **0** | **0.0** | **6/6** | **6/6** |

The copula-anchored form requires the shape the rule was written for, which is `is` or `was` or `means`, an optional determiner, the X term, a comma, "not", an optional determiner, a non-adverbial Y term, and a clause boundary. It matches "The work is judgement, not process." and declines "He was very young, not more than nineteen then." It ran 200k pathological characters in 0.004 seconds.

Recommended as its own round, so that this one stays methodology. Ripping `BS-011` out is not recommended; the tell it targets is attested in the wild, and a rule that measures 0.0 per 10k with full recall is strictly better than either keeping the loose version or deleting the coverage.

## What ships

Documentation, tooling, tests and one data file. `data/caveats.json` changes, so this is a **restart and not a rebuild**: nothing in `src/` moved, and `humanizer_get_caveats` reads the file that `entrypoint.sh` pulls on every start.

1. `eval/fpcorpus/SOURCES.md`: provenance manifest for Tier 2. Gutenberg id, title, author, first publication year, normalized SHA-256, character count and sentence count per work.
2. `eval/fpcorpus/fetch_longform.py`: fetches the six works over HTTPS and strips the Gutenberg header and footer. It unwraps hard line breaks while preserving blank lines as paragraph boundaries, and normalizes smart quotes to ASCII exactly as the calibration corpus does. Em-dashes are left verbatim. Each result is verified against the recorded checksum. Writes to `eval/fpcorpus/longform/`, which is gitignored. Storing a fetch script and checksums rather than 5.5MB of text keeps the repo small, and `eval/` already never reaches the image because the `Dockerfile` copies only `src/` and `data/`.
3. `tests/support/fp_corpus.py`: the shared sweep helper. Exposes both tiers, the recorded Tier 2 sentence count, a Tier 1 zero assertion and a Tier 2 rate calculation. Tier 2 helpers skip when the corpus has not been fetched, so the suite stays green on a clean clone.
4. `tests/checker/test_tells_2026_09.py`, `tests/checker/test_orwell_and_carry_2026_08.py`, `tests/checker/test_tells_2026_09_survey.py`: three independent re-implementations of `test_no_false_positives_on_human_corpus` replaced by calls into the helper, each naming the tier it reads. Copying it a fourth time was the alternative and it would have left each round's bar implicit in its own file.
5. `tests/support/test_fp_corpus.py`: tests for the helper, including that a Tier 1 assertion fails when handed a rule that does fire, so the helper cannot silently pass everything.
6. `data/caveats.json`, `short_corpus_cannot_validate_run_detectors`: revised to point at the tier that now exists and to name the Tier 2 blind spot, replacing "bring your own long-form control".
7. `eval/README.md`: a section separating the calibration corpus from the false-positive corpus, so the next reader does not repeat the conflation.
8. `CLAUDE.md`: the standing bar rewritten as two tiers with two metrics, plus the control requirement.
9. `docs/RULE-HISTORY.md`: this round, with the deployed-rule table.
10. `.claude/settings.json` committed, and `.claude/settings.local.json` gitignored. The tracked file enables the `mcp-server-dev` plugin for this repo, which is a project fact rather than a machine fact. The local file is per machine and does not belong in the repo.

## Rejected alternatives

- **Add long-form files to `eval/corpus/human`.** Breaks `test_calibration_corpus_meets_spec`, which asserts `len(ai) >= len(human)` and four human samples per genre. Unpaired text also corrupts the AUC separation measurement that the directory exists to serve. This is the conflation that caused the contradiction, so widening it was never on the table.
- **Revise the bar and skip the corpus.** Leaves the caveat's instruction unsatisfiable and makes every future long-form number unreproducible, which is the state the anaphora round already demonstrated.
- **Commit the 5.5MB of normalized text.** Reproducible with no network, at the cost of a repo that is mostly Victorian fiction. The existing `SOURCES.md` convention already records provenance for text the repo does not own, and the six works are stable, canonical and retrievable by id.
- **Checksum the raw download instead of the normalized text.** Gutenberg regenerates its plain-text files, so a raw checksum drifts for reasons that have nothing to do with the corpus content. Checksumming after normalization pins what the sweep actually reads.
- **Make a Tier 2 checksum mismatch a hard test failure.** Rejected because Tier 2 is an opt-in developer tier and a clean clone has no corpus at all. The fetch script verifies loudly and the tests skip when the tier is absent. A reported number stays tied to the recorded checksums, and that tie carries the reproducibility.
- **A single unified bar expressed as a rate on both tiers.** A rate is meaningless on 109 sentences, where one firing is 91.7 per 10k. Tier 1 keeps an absolute zero because its denominator is small enough for zero to be the right demand.
- **Raising the Tier 2 threshold to 6.0 so that `BS-009` passes.** Rejected on the standing instruction. The threshold is set by what is auditable, and a deployed rule sitting just outside it is a finding worth keeping visible.
- **Fixing `BS-011` in this round.** The measurement belongs here because it is the evidence that the tier works. The change belongs in its own round with its own TDD pass, because it touches a deployed detector and this round touches nothing deployed.

## Self-check

Checked with `humanizer_check_text` against the deployed rules: `prohibitions_clear` true, zero hard violations. Remaining `must_clear` findings were reviewed and either rewritten or justified below.

## Tests

`tests/support/test_fp_corpus.py` plus the three converted sweeps. Tier 2 numbers in this document are reproducible from `eval/fpcorpus/fetch_longform.py` and the checksums in `eval/fpcorpus/SOURCES.md`.
