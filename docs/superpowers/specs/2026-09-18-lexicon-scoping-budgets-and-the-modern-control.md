# Lexicon scoping, document budgets, and making the modern control re-runnable

Round date: 2026-09-18, third of the day. Status: shipped. **Deploy class: rebuild**, because `src/checker/budgets.py`, `loader.py` and `__init__.py` change. Everything else in the round is data.

## What this round closes

Five loose ends, four of them left by earlier rounds of the same day and one by 2026-08-10.

1. The always-on instruction surface for this directory has never met its budget.
2. The modern-register control that decided the `BS-011` round existed only as a scratchpad script.
3. `BS-005` sits at 1.9 per 10k and the two-tier round recorded that it fires on ordinary participles.
4. The lexicon round said a lexicon must be compared **per term**, and did not do it.
5. `per_section_checks_miss_document_budgets` said the mechanical fix was scoped out rather than rejected, and it stayed scoped out for five weeks.

## 1. The context budget

`.claude-context-budget` now sets 4600 against 4,453 measured. The file carries the arithmetic: of the 4,453 only 1,699 is this repo's `CLAUDE.md`, and 2,754 is the global half that no edit here can touch, so the default 4000 demanded 1,246 tokens of project instructions. That is less than the deploy rules, the false-positive discipline and the two-tier bar cost to state once. The file also records what is still owed and why it is an operator call rather than hygiene.

## 2. The modern control, re-runnable

`eval/fpcorpus/modern_control.py` makes the measurement that decided the `BS-011` round repeatable. It is a **control and not a third tier**, and the module says so in its own docstring. There is no standing rate bar and nothing gating a round. A `prose_only` view drops the documents which quote patterns as data: round specs, the rule history, the proposals, the sibling changelog. On this round's run that split is 37 firings across everything against 9 in prose only, which is the bias made visible rather than argued about.

Found while testing it, and worth recording because it generalizes: **the impossible-pattern sentinel a round uses as its must-be-zero control gets written into that round's own spec, and then fires here.** `zzqqxx` returns 2 hits on this corpus today. Pick a fresh sentinel per round.

## 3. BS-005, tightened

`,\s+(contributing|underscoring|highlighting|reflecting|setting|marking|emphasizing|showcasing|demonstrating|reinforcing|paving|ushering)\b\w*` returned 9 firings, 1.9 per 10k, every one an ordinary participle: "setting aside his bread and butter", "reflecting on what she had heard", "emphasizing each slow down-stroke".

Two moves, both from reading the firings. `setting` and `marking` are **dropped**, because their attested forms are already `BS-004` ("setting the stage for", "marking a pivotal moment", verified firing in the same run) while their bare forms are ordinary English. `reflecting` and `emphasizing` are **scoped to an abstract complement**, because the human uses take a concrete one.

Measured, one run: **9 firings to 0, 1.9 to 0.0 per 10k**, Tier 1 clear, 6/6 on constructed tells, 5/5 on the Victorian participles above, and the two `BS-004` forms still caught by `BS-004`.

## 4. The lexicon, per term

The previous round accepted `flagged_term` at 34.8 per 10k and said the comparison had to be per term. Done here, across all 120 groups on both tiers plus the modern control.

**Eight terms exceed 5.0 per 10k on their own**: `particularly` 24.8, `Moreover` 9.6, `Consequently` 8.3, `endeavor` 8.3, `boast` 7.4, `elevate` 7.4, `landscape` 6.8, `commence` 6.6. The other 112 are under, and 31 fire only in modern prose, which is a lexicon working correctly.

The eight split into three kinds, and the split is the finding.

**Register artifacts, kept**: `Moreover`, `Consequently`, `endeavor`, `commence`, `ascertain`. Attested tells in 2026 prose, absent from Tier 1 (0 hits on all of them), and common in Victorian formal writing. The gap between the tiers is the evidence they are right, not that they are wrong.

**Collocational tells, scoped and moved out of the lexicon**: `boast`, `elevate` and `landscape` become `BS-049`, `BS-050` and `BS-051`. Their own lexicon entries already carried the scope in prose: "Marketing ('elevate your X')", "Flagged when used metaphorically. Literal geographic use is fine." The round mechanizes those notes, which is the `BS-033` treatment that scoped `quiet`. Measured: `boasts a/an/over X` 0.2 per 10k, `elevate your X` 0.0, the metaphorical landscape 0.0, against 7.4, 7.4 and 6.8 for the bare words; recall 8/8 on constructed marketing positives, 8/8 on Victorian negatives ("a man not given to boast of his courage", "the engineers elevated the track above the river", "the landscape was bare and white with snow").

**A generic intensifier, dropped**: `particularly`, severity low, 117 occurrences on Tier 2 and one each on Tier 1 and in plain modern prose. It produced 18 percent of every lexicon finding on human prose, and its offered replacements (`especially`, `mainly`, `above all`) are synonyms of it rather than the specific claim the guidance asks for. The section it sat in already makes the real point in prose, that the model underuses manner and degree adverbs and reaches for generic intensifiers, and that is a rubric matter. `significantly` and `effectively` stay: both are inside the bar and both carry "or quantify it" as an alternative, which is a real instruction.

## 5. Document budgets, mechanized

`caveats.per_section_checks_miss_document_budgets` was found on a 39-page case study where one shape had been justified four separate times, once per section, and it recorded that a document-level count was scoped out rather than rejected.

It now exists for the shapes a detector can find. `banned_structures` entries carry a `document_budget` field (`BS-011`, `BS-018`, `BS-038`, `BS-039`, all 1), `loader.load_document_budgets` reads it, and `src/checker/budgets.py` emits a `document_budget` finding when a budgeted shape appears more often than its budget in one call. The individual findings are still reported, because a writer needs the offsets.

**The protocol requirement is unchanged, and the finding says so in its own text.** The checker sees only the text it is handed, so a section-by-section walk still under-counts and the last run still has to be on the assembled document. The requirement now has an instrument, which it did not before.

The judgment-bound budgets stay in the rubric: the appositive significance label, the aphorism, the anaphoric run. A detector that cannot find one instance cannot count three.

Measured on the same run: **0 budget findings on Tier 2** (all six works) and **0 on Tier 1** (16 files). Two of the 15 files in the plain modern control fire, both on `BS-011`, and both are documents that discuss the contrastive construction. That is the accepted false positive from the earlier round compounding, not a new one.

## Controls

Run in the same invocation as every number above: `BS-004` fired on both forms `BS-005` gave up, which is the discriminating positive for the drop; the deployed lexicon reproduced its recorded 164 findings and 34.8 per 10k before any term was removed; and the budget counter returned nothing for `BS-006`, a rule with no `document_budget`, in a test that hands it five findings.

## What ships

`.claude-context-budget`; `eval/fpcorpus/modern_control.py` and `tests/support/test_modern_control.py`; `data/banned_structures.json` (`BS-005` narrowed, `BS-049` to `BS-051` added, four `document_budget` fields); `data/lexical_patterns.json` (four entries removed); `data/caveats.json` and `data/self_review.json`; `src/checker/budgets.py`, `loader.py`, `__init__.py`; `tests/checker/test_document_budgets.py` plus edits to two existing lexicon tests; `docs/DATA_SCHEMA.md`, `docs/API_SPEC.md`, `docs/RULE-HISTORY.md` and `eval/fpcorpus/SOURCES.md`.
