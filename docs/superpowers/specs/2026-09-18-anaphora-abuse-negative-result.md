# Anaphora abuse: a recorded negative

Status: **rejected, do not re-attempt without new evidence.** No rule ships. The round produces one `self_review.json` judgment item, two `caveats.json` entries, and a negative regression test.

## Trigger

`docs/superpowers/specs/2026-09-17-copula-avoidance-and-2026-survey-design.md` recorded anaphora abuse (three or more consecutive sentences opening on the same word) as **scoped out rather than rejected**, on the grounds that it needs a detector in `src/checker/structures.py` (a rebuild rather than a restart) and that `The X … The Y … The Z …` is ordinary paragraph construction. This round is that follow-up. It went looking for a formulation that clears the standing bar and did not find one.

The attested tell, from the in-the-wild report:

> They assume users will pay. They assume the market is ready. They assume nothing changes.

`BS-009` (`this_chain`) already detects exactly this shape for `This`/`These`/`It` only, at a threshold of three. The proposal was to generalize it to any opening word.

## The measurement that decided it

### The eval corpus cannot see this rule at all

The standing bar for a round is 0/16 structural false positives on `eval/corpus/human`. Every candidate formulation scored 0/16, including the loosest one tested (same first word, threshold three, no guards at all).

That result is worthless. The human corpus is **16 files, 109 sentences in total, a mean of under 7 sentences per file**. A detector that needs a run of three consecutive sentences inside one paragraph has almost no room to fire in a 7-sentence document, so 0/16 is a trivially satisfiable pass rather than evidence of precision. A control confirmed the probe pipeline was working: the attested positive above fires on eight of eight formulations, so the zeros were real; the probe was sound.

This is the `flow_over_surface_features` failure mode in reverse: not a rule that cries wolf, but a bar that cannot be failed. It is recorded as its own caveat, because it applies to every future run-length or cross-sentence detector, this one included.

### Measured against prose long enough to answer

To get a number, the probe ran against six public-domain works (*Bleak House*, *Pride and Prejudice*, *Moby-Dick*, *Walden*, *Tom Sawyer*, *The Adventures of Sherlock Holmes*): 5.48M characters, **47,088 sentences**, all of it unambiguously human and all of it pre-1930, so there is no possibility of model contamination. Paragraph-bounded, markdown chrome skipped.

| Formulation | FP on 47k human sentences | per 10k sentences | Recall on constructed positives |
|---|---|---|---|
| same 1st word, n=3 | 355 | 75.4 | n/a |
| same 1st word, n=4 | 105 | 22.3 | n/a |
| non-determiner 1st word, n=3 | 282 | 59.9 | n/a |
| subject pronoun only, n=3 | 211 | 44.8 | n/a |
| subject pronoun only, n=4 | 63 | 13.4 | n/a |
| same first TWO tokens, n=3 | 65 | 13.8 | 6/6 |
| subject pronoun + same 2 tokens, n=3 | 35 | 7.4 | 4/6 |
| same first TWO tokens, n=4 | 11 | 2.3 | **0/6** |
| + skip dialogue (best case) | 29 | 6.2 | 4/6 |
| **same 2 tokens, n=3, every sentence ≤10 words** | **15** | **3.2** | **6/6** |

Each of the candidate angles named in the proposal was tried. Requiring a determiner-free subject pronoun cuts false positives by half and costs recall, because the attested tell class includes `The platform scales. The platform adapts.` Requiring the same two opening tokens rather than one is the single most effective guard. Excluding dialogue barely helps: 35 to 29. Raising the threshold to four destroys the motivating example: the attested tell is three sentences long, so n=4 scores 0/6 recall **while still producing false positives**, which is the clearest dead end in the table.

### The surviving false positives are the rule's own refutation

The best formulation is same-first-two-tokens, threshold three, every sentence at most ten words: 3.2 per 10k sentences, 6/6 recall. All fifteen of its false positives were read. Not one is a defect. Most are deliberate, celebrated anaphora:

- Thoreau, *Walden*: `It does not keep the country free. It does not settle the West. It does not educate.`
- Melville, *Moby-Dick*: `Forty years of continual whaling! Forty years of privation, and peril, and storm-time! Forty years on the pitiless sea!`
- Dickens, *Bleak House*: `As my father's came there. As my brother's. As my sister's. As my own.`
- Doyle: `In the dress is a pocket. In the pocket is a card-case. In the card-case is a note.`

Set Thoreau beside a constructed positive from the same probe:

| | |
|---|---|
| Attested AI tell | `It reflects the brief. It reflects the budget. It reflects the deadline.` |
| Thoreau, *Walden* | `It does not keep the country free. It does not settle the West. It does not educate.` |

Three sentences. Subject pronoun plus a repeated verb. Under eight words each. Paragraph-internal. **Every property a detector can read is identical.** What separates them is whether the repetition is doing rhetorical work: a judgment about whether the escalation earns itself, which no property of the string records.

This is the same wall the appositive label hit twice (`labels_are_where_the_tells_hide`), but a harder version of it. There the missing information was part of speech, which a parser would supply. Here no parser helps, because the two cases are *syntactically the same construction*. Anaphora is a named rhetorical figure. The tell is not a distinct shape; it is the figure used without purpose.

### Precision, stated plainly

On human prose every firing is a false positive by construction, so the honest framing is the rate and the read. Fifteen firings, fifteen legitimate passages: **0/15 precision** at the best operating point. The appositive label was rejected at 1/14. This is worse, and unlike that case there is no residual angle left untried.

In practical terms 3.2 per 10k sentences means a spurious must-clear finding in roughly one of every ten 300-sentence documents. Each one asks an author to justify a passage that is fine. Worse, it asks most often of the authors writing most deliberately, since the rate rises with rhetorical ambition. `over_regularization_caveat` and `uniform_application_paradox` both point the same way: a rule that fires on Thoreau is a rule that flattens good writing toward the mean.

One confound is stated rather than hidden. The ≤10-word gate is the guard that makes the best row look shippable, and the positive set it scores 6/6 against was **written for this probe by the same author**. Its shortness is an artifact of how the examples were composed rather than a measured property of model anaphora. The gate is therefore weaker than the table suggests, and the real recall of that row is unknown. A round that wanted to revisit this would need a corpus of attested model anaphora in the wild first. That, and not another formulation, is the missing input.

## A finding about the rule already deployed

Run against the same 47k human sentences, the **existing** `BS-009` produces **27 findings, 5.7 per 10k**, the same order of magnitude as the best new candidate, and higher than several formulations rejected here. Twelve are in *Walden* alone, including the Thoreau passage above, which `BS-009` already flags today. It flags the attested model tell `It reflects the brief. It reflects the budget. It reflects the deadline.` too. So inside the one slice that *is* mechanized, the figure and the tell are already indistinguishable in practice as well as in principle. Both are pinned by the negative test.

Nothing is changed in response to this. `BS-009` is `gate=checklist`, so a false positive costs an author one justification rather than a blocked build, and the rule has been in place across every round since. But it is the reason the generalization is not worth shipping: widening the opener set from three words to all words multiplies an already-measurable false-positive cost across the whole language, in exchange for a tell the `self_review` rubric can carry. The finding is recorded in the caveat so that the next round starts from the measured number rather than from the untested assumption that `BS-009` is clean.

## What ships

Data-only. No detector, no regex, therefore **no rebuild**: restart only, and the ReDoS bar is not applicable because no pattern was added.

1. `data/self_review.json`: a new judgment item, anaphora and repeated sentence openings, written so the definitional caveat is inseparable from the check: the form is legitimate and the tell is purposeless repetition. Names the attested forms, and the budget.
2. `data/caveats.json`, `rhetorical_figures_defeat_shape_detection`: a deliberate figure and its abusive twin are the same construction, so shape detection cannot separate them; includes the Thoreau/AI pair and the 0/15 number, and the `BS-009` 5.7-per-10k measurement.
3. `data/caveats.json`, `short_corpus_cannot_validate_run_detectors`: `eval/corpus/human` averages under 7 sentences per file and cannot falsify any cross-sentence or run-length rule; such a round must bring a long-form control, and 0/16 on this corpus must not be reported as evidence for one.
4. `tests/checker/test_anaphora_negative.py`: a negative regression test pinning the attested anaphora shape, the Thoreau passage and three other human passages as **unflagged by any structure**, so a later round cannot reintroduce this by accident. Precedent: the appositive-label negative test.

## Rejected candidates, for the record

- **Same opening word, any threshold.** 75.4 per 10k at n=3; 22.3 at n=4. Ordinary paragraph construction, exactly as the previous round predicted.
- **Determiner-free subject pronoun.** Halves the rate, still 44.8 per 10k, and excludes the attested `The platform scales…` class.
- **Threshold of four.** 0/6 recall against the attested three-sentence tell, and still firing on human prose. Strictly dominated.
- **Excluding dialogue and quoted speech.** 35 to 29. The false positives are mostly narration rather than dialogue.
- **A ≤10-word staccato gate.** The best row in the table, and the one whose recall is confounded by a self-authored positive set. Not shippable on that evidence.
- **Requiring the second token to be a verb** (so `They assume` matches but `The Adventure of` does not). Needs part of speech. The same parser the server does not have, and the reason `labels_are_where_the_tells_hide` exists. Thoreau's passage is pronoun-plus-verb anyway, so it would not help.
- **A density gate** (flag only clustered runs, as `rule_of_three_density` does). Rejected on the same reasoning as in the candour round: a density gate works when individual instances are legitimate and the clustering is the signal. Here individual precision is already 0/15, and Dickens clusters anaphora deliberately: the shop-inscription catalogue is five consecutive sentences. Clustering selects *for* the literary case.

## Self-check

This document checks `prohibitions_clear: true`, zero hard violations, against the deployed rules. Two `must_clear` findings remain and are **justified rather than cleared**: both are `BS-009` firing on the document's own quotation of the attested tell (`It reflects the brief. It reflects the budget. It reflects the deadline.`). That quotation is the evidence the round turns on, and removing it to satisfy the checker would delete the finding. Noted here so a later reader does not mistake it for an unresolved item. Nine other findings from the first pass were real and were fixed, including six instances of the same `X, not Y` construction, which is `self_review` item 3 working as intended on its own design doc.

## Tests

`tests/checker/test_anaphora_negative.py`. The probe scripts are dev-only and not committed; the numbers above are reproducible from the six Gutenberg ids recorded in the test module docstring.
