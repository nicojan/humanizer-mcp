# The four rules over the Tier 2 rate: one tightened, three recorded

Round date: 2026-09-18, immediately after the `BS-011` copula anchor. Status: shipped, data only. `src/` is untouched, so the host restarts and does not rebuild.

## What this round answers

The two-tier round measured all 48 deployed rules on 47,088 sentences of pre-1930 prose for the first time and found five above the 5.0 per 10k threshold. It changed none of them, on the standing rule that a retroactive failure is a finding rather than a mandate. `BS-011` was handled in its own round. This round takes a decision on the other four and writes each one down, because an unexplained number invites the next round to rediscover it.

Every number below comes from one invocation of the shared sweep in `tests/support/fp_corpus.py`. The controls in that run: `BS-006` fired 94 times, reproducing the recorded figure exactly, and the freshly narrowed `BS-011` returned 0, which is the must-be-zero. A sweep that cannot fire and a sweep that found nothing produce identical output, so both were needed.

| rule | firings | per 10k | deploy class | decision |
|---|---|---|---|---|
| `flagged_term` (lexicon) | 164 | 34.8 | data | accept, and correct the metric |
| `rule_of_three_density` | 97 | 20.6 | detector | accept, already predicted |
| `BS-006` `negative_parallelism` | 94 | 20.0 | data | **tighten to 7 firings, 1.5 per 10k** |
| `BS-009` `this_chain` | 27 | 5.7 | detector | unchanged, decided 2026-09-18 |

## BS-006: tightened

The deployed pattern is `\bnot (just|only)\b[^.?!]{0,60}?\bbut\b`. Of its 94 firings, **93 are `not only ... but`** and exactly one is `not just`. The correlative `not only X but Y` is ordinary English and Victorian prose reaches for it constantly: "I was not only instructed in everything that was taught at Greenleaf, but was soon engaged in helping."

The attested tell, `AP-006`, is `not just X, but also Y`. So the pattern was tightened to require either the modern `just` form or the explicit `but also` correlative:

```
\bnot just\b[^.?!]{0,60}?\bbut\b|\bnot only\b[^.?!]{0,60}?\bbut also\b
```

Measured, one run: **7 firings, 1.5 per 10k** (from 94 and 20.0), Tier 1 clear either way, 4/5 recall on a constructed set of the tell, and all three Victorian negatives above now declined where the deployed pattern declined none. Two other formulations were probed and rejected: dropping `only` altogether scores 0.2 per 10k but only 3/5 recall, and shortening the window to 25 characters keeps 5/5 recall at 10.6 per 10k, still twice the bar.

All 7 survivors were read. Every one is the `not only ... but also` correlative in a long human sentence (Melville's seals, Conan Doyle's Cuvier), so precision is 0/7 and the narrowing buys volume rather than a clean separation. It ships because a thirteen-fold reduction with one recall step lost is worth taking at `gate: checklist`.

The recall step lost is the bare correlative used as a flourish, `This is not only a design problem but a cultural one.`. That form stays in the self-review rubric's antithesis item and in the sibling prompt's antithesis family, which is where the unmechanizable half of this family already lives.

## flagged_term: accepted, and the metric corrected

164 findings, 34.8 per 10k, 655 word occurrences. The largest contributors are `particularly` (117 occurrences), `Moreover` (45), `Consequently` (39), `endeavor` (39), `boast` (35), `elevate` (35), `landscape` (32) and `commence` (31). Reading them settles what they are: ordinary formal vocabulary in its pre-tell sense, which is `over_regularization_caveat` working exactly as it describes.

**The rate as measured is the wrong number for this rule, and that is the finding.** The 5.0 per 10k threshold was set by what one person can audit for a single detector: about 24 firings. `flagged_term` is not one detector; it is roughly 120 lexicon groups sharing a finding type. Per group the rate is **0.29 per 10k**, two orders below a single rule's threshold. A future round must compare a lexicon per term, not per layer.

Two further facts settle the decision. The same lexicon fires **10 times on Tier 1** (109 sentences of modern human prose), on `Additionally`, `foster`, `innovative`, `facilitate`, `harness`, `cornerstone`, `boast`, `particularly`, `refine` and `differentiate`, each once or twice. The behaviour is therefore register-independent and known rather than a Victorian artifact. The tell these words carry is also frequency and clustering rather than collocation. The `BS-033` treatment that scoped `quiet` to `quiet X` works because that word's tell **is** a collocation. `delve` and `bolster` are flagged for something else: how often they cluster, and how rarely a human reaches for them in 2026. `content_profiles` and the `severity` field already carry the register adjustment, and `gate: checklist` means the cost of a firing is one justification.

Recorded as `caveats.lexicon_rate_is_not_a_detector_rate`.

## rule_of_three_density: accepted, already predicted

97 findings, 20.6 per 10k, 31 in *Bleak House* and 36 in *Moby-Dick*. Reading them settles what they are: catalogues and triadic description. The shop-inscription list, "short, cadaverous, and withered", the stationer's inventory of foolscap and brief and draft and brown and white. `caveats.rhetorical_figures_defeat_shape_detection` predicted exactly this before the sweep ran, for the same reason it rejected the anaphora rule: the deliberate figure and its machine twin are one construction, and the difference is whether the third item earns itself.

Tightening was not attempted, because the only readable knobs are the item count and the clustering window, and both were already probed when the detector shipped in June. The detector is `gate: checklist` and lives in `src/checker/structures.py`, so changing it would also cost a rebuild for a rule whose firings a reader can dismiss in a second. The number is recorded in the caveat instead.

## BS-009: unchanged, and not re-litigated

27 findings, 5.7 per 10k, reproducing the anaphora round's figure exactly. That round read the firings, found twelve of them in *Walden*, and kept the rule deliberately. It is narrow and `gate: checklist`, and the alternative was widening the opener set to the whole language. No new evidence appeared in this round, so nothing changed. `caveats.rhetorical_figures_defeat_shape_detection` already carries the reasoning.

## What ships

1. `data/banned_structures.json`, the `BS-006` pattern and description.
2. `data/caveats.json`, a new `lexicon_rate_is_not_a_detector_rate` entry, and the `rule_of_three_density` measurement appended to `rhetorical_figures_defeat_shape_detection`.
3. `tests/checker/test_tier2_rate_decisions_2026_09.py`.
4. `docs/RULE-HISTORY.md`, one round entry and one index line.

No sibling change. The prompt carries the antithesis family as judgment and already lists both forms, so a mechanical narrowing on the server does not narrow the guidance a reader applies.
