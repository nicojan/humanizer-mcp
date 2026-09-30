# BS-011: the copula anchor, and the hole the Victorian corpus could not show

Round date: 2026-09-18. Status: shipped, data only. Deploy class: `data/banned_structures.json`, `data/caveats.json` and `data/self_review.json` change, `src/` does not, so the host restarts and does not rebuild.

## The problem

`BS-011` `x_not_y_contrastive` is deployed as `\b\w+,\s+not\s+\w+`, `confidence: low`, `gate: checklist`. On Tier 2 (47,088 sentences of pre-1930 prose) it fires **358 times, 76.0 per 10k**, the worst rate of any deployed rule and fifteen times the 5.0 bar. Its firings are ordinary negation: `not yet decided`, `not more than nineteen`, `not seated, but standing`. It declines **1 of 6** constructed hard negatives.

The previous round measured a copula-anchored replacement at 0 firings on Tier 2 and recommended it for its own round. This is that round, and it starts by trying to falsify that recommendation rather than by shipping it.

## The three formulations, one invocation

Probe script: `eval` was not touched; the probe ran the three patterns plus two controls over Tier 2, Tier 1 and a modern control in a single run, with `re.IGNORECASE`, which is what `find_regex_structures` applies.

| | Tier 2 firings | per 10k | Tier 1 | modern control | attested 6 | hard negatives |
|---|---|---|---|---|---|---|
| deployed `\b\w+,\s+not\s+\w+` | 358 | 76.0 | 1 | 92 (341.8 per 10k) | 6/6 | 1/6 |
| clause-final Y, adverbials blocked | 9 | 1.9 | 1 | 23 (85.4 per 10k) | 6/6 | 5/6 |
| **copula anchor plus clause-final Y** | **0** | **0.0** | **0** | **9 (33.4 per 10k)** | **6/6** | **6/6** |

Controls in the same run, as the standing bar requires: the deployed pattern reproduced its recorded 358 firings and its 76.0 rate exactly, which is the discriminating positive; a deliberately impossible variant (`\bzzqqxx,\s+not\s+zzqqxx\b`) returned 0 on all three sets, which is the must-be-zero; and 200,000 pathological characters matched in 0.0035s, so the anchored pattern is ReDoS-safe.

## The hole, measured

Tier 2's zero is real and it is measured in Tier 2's documented blind spot. Victorian fiction does not write `The tell is the appending, not the phrase.` because it is not writing rules about its own prose. Modern editorial and technical prose does.

The modern control is 30 markdown files already on disk: this repo's `docs/`, its specs, `CLAUDE.md` and `README.md`, plus the sibling `~/code/humanize-text-prompt/*.md`. **2,692 sentences** by `src.checker.segment.split_sentences`. The copula anchor fires **9 times, 33.4 per 10k**, more than six times the Tier 2 bar.

Read of all nine:

1. `is the appending, not the phrase.` (DATA_SCHEMA)
2. `is judgment, not a detector;` (DATA_SCHEMA)
3. `is collocation, not the word.` (proposed-rules-2026-07-25)
4. `are a finding, not noise.` (eval methodology spec)
5. `is dropped, not guessed.` (corpus construction spec)
6. `is judgement, not process.` (two-tier spec)
7. `is data, not code.` (CLAUDE.md)
8. `is the collocation, not the word.` (PROMPT.md)
9. `is the appending, not the phrase.` (PROMPT.md)

Number 6 is the round's own attested positive quoted as evidence, so it is a true positive. The other eight are the same rhetorical act: fixing the scope of a rule that was just stated. **Precision 1/9.**

Two further facts sharpen it. Split by whether the file is prose *about* this construction, 8 of the 9 are in meta-text and 1 is not, so the control is a biased sample rather than a representative one. And the pattern fires on any copula corrective identification, which a constructed probe confirmed: `The response was 406, not 421.`, `The file is JSON, not YAML.`, `The winner is Maria, not Tom.` all fire.

## Recall is narrower than 6/6 suggests

The six attested tells recorded last round are all copula plus noun plus clause-final Y, which is the shape the candidate was built around. Scored against contrastive tells outside that shape, the copula anchor keeps **1 of 5**:

| sentence | deployed | clause-final | copula anchor |
|---|---|---|---|
| `The brush-stroke wordmark comes from paint on paper, not the polished apps she gave up on.` (AP-005, the rule's own source example) | fires | no | **no** |
| `We chose depth, not breadth.` | fires | no | no |
| `The aim is speed, not polish, and that shapes every decision.` | fires | no | no |
| `It was a conversation, not an interrogation.` | fires | fires | fires |
| `Good design rewards patience, not speed.` | fires | fires | no |

So the change is a deliberate precision-for-recall trade, and the recall it gives up includes `AP-005`'s own before-text. That cost is paid explicitly below rather than discovered later.

## Decision

**Ship the copula anchor as `BS-011`, accept the corrective-identification false positive in the entry, and move the coverage that narrows away to the self-review rubric.**

Four findings drove it, in the order they were decided.

**Narrowing further was attempted and does not separate the two senses.** The attested tells and the scope notes are the same construction: `The work is judgement, not process.` against `The tell is the appending, not the phrase.`. Determiners do not split them. The attested six run 4 bare and 2 determined; the eight false positives run 3 bare and 5 determined. Sentence position does not split them either. Nor does a prestige-noun lexicon, because `is judgment, not a detector` puts a prestige abstraction on the X side of a false positive. What separates the two is whether the sentence performs an insight or fixes a referent, and the string does not record that. `rhetorical_figures_defeat_shape_detection` covers the same failure in a second construction.

**Rejecting and leaving the deployed rule at 76.0 per 10k is worse than shipping.** The copula anchor beats the incumbent on every axis measured: 0 against 358 on Tier 2, 9 against 92 on the modern control, 6/6 against 1/6 on hard negatives, with the same 6/6 on the attested tells. Leaving a strictly dominated rule deployed because its replacement is imperfect keeps the worse precision and the worse recall profile at once.

**The accepted cost is one justification.** `BS-011` is `gate: checklist` and `confidence: low`, so a firing asks a writer to look and justify, and it does not block anything. Nine findings per 2,692 sentences of rule-writing prose is a cost this repo will pay on its own documentation, knowingly, and the entry now says so.

**Deleting `BS-011` was never on the table.** The tell is attested (`AP-005`) and deleting the coverage is worse than either shipping or rejecting.

## No third tier

The modern control stays a one-off control recorded here, and it does not become Tier 3.

Three reasons. The sample is **biased by construction**: 8 of its 9 firings are in prose about this very pattern, and a tier built from the repo that writes the rules would certify rules against their own idiom. A tier carries a **standing rate bar and a maintenance cost**, and the last round's finding was precisely that a tier's zero means nothing outside its register, so adding a third biased tier would license more false confidence rather than less. And the modern prose that would make an unbiased tier is **still in copyright**, which is why Tier 2 is Victorian in the first place.

The artifact that ships instead is durable in a way a corpus directory would not be. The eight accepted false positives are **pinned as tests** that assert the rule does fire on them, so the accepted cost stays visible in the suite. A later round that believes it has narrowed the rule has to make those tests fail on purpose and say why.

## What ships

1. **`data/banned_structures.json`**, `BS-011` pattern replaced by the copula anchor, description rewritten to name the frame and the accepted false positive. `gate` and `confidence` unchanged.
2. **`data/self_review.json`**, a new item covering contrastive `X, not Y` outside the copula frame, which is the recall the mechanical rule gives up.
3. **`data/caveats.json`**, `contrastive_scope_notes_are_the_same_shape` records the measurement, the 1/9 precision read, the biased-sample finding and the no-third-tier decision.
4. **`tests/checker/test_bs011_copula_anchor.py`**, with the Tier 1 and Tier 2 sweeps through `tests/support/fp_corpus.py`, the recall set, the hard negatives, the accepted false positives, and the discriminating controls.
5. Sibling `~/code/humanize-text-prompt`, whose antithesis section does not list the inline copula form.

`caveats.per_section_checks_miss_document_budgets` still names `BS-011` as carrying the one-per-document antithesis budget, and that is still true: the rule is narrower, and the budget it carries is unchanged.
