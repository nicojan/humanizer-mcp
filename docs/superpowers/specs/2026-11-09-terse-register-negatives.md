# Terse-register hard-negative set (2026-11-09)

## Why

Three rule rounds running (2026-09-29, 2026-10-30, 2026-11-09), an independent adversarial review found false positives that Tier 1 and Tier 2 could not show. Both tiers are long-form prose, and the candidates were label, caption, cell or slogan shapes. The clearest case came earlier the same evening: a numeral-contrast caption rule scored zero on four corpora with a control firing, then flagged about 100 ordinary lines ("Two tablets, every four hours.", "Two adults, one child."). Each round wrote its own negatives from scratch. This round makes them a shared, committed set.

## The set

`eval/fpcorpus/terse/`: 299 lines in 13 registers, about 22 each. Claude wrote the first 260 lines. An independent agent then read every line for realism and for AI tells of its own. It rewrote 18 (prescription labels use numerals and a verb; real headlines carry no full stop; five number pairs read as taglines, not functional writing) and suggested 36 lines with harder adversarial shapes: "TL;DR:", "Bottom line:", "Here's the thing:", "Not urgent, but can you look today?", "At a glance", "Why selling? Downsizing.". One disagreement: the reviewer wanted the weather line out of meeting notes, and it moved to headlines instead, because weather desks really write it.

It is a standing bar and not a tier. No regex structure may fire on any line, the full checker in label mode may report nothing but AR-003's missing full stop, and each register read as one document may trip no run-length, budget or density rule. The control is the rejected caption pattern, which fires on 14 lines in six registers.

## What the first run found

All 56 regex structures were swept, plus the full checker on every line and on every register as a document.

1. **`BS-062` fired on "Looking ahead, the forecast calls for rain through Thursday."** Its date guard spared a month or a digit but not a weekday. It now also spares weekdays, "today", "tonight", "tomorrow" and "weekend". The existing positive ("Looking ahead, the family hopes to open a second shop.") still fires.
2. **`BS-062` was quadratic in production.** For each "Looking ahead," the date guard scanned to the end of the sentence and then backtracked through every month name at each position. On text with no full stops that meant the whole input, so the rule took 9.6 seconds at the 100k-character cap on `main`. The guard now reads at most the next 200 characters of the sentence: 0.11 seconds worst case. The 2026-10-30 review had fixed the paragraph lookahead and missed this one, because its attack text was not the rule's own trigger repeated. A sweep of all 56 rules with each one's anti-pattern example repeated to the cap found no other slow rule. The spec bar now asks for that trigger-repeat timing.
3. **`BS-024` fired on the headline "Not a recession, but close, economists say".** A trailing attribution with no full stop is how headlines are written, and the story names the sources, so "name the source" is the wrong fix. The rule now declines a comma, a group noun, "say" or "says", and the end of the line. "Remote work boosts productivity, experts say." with its full stop is body prose and still fires, as do "experts argue" and the sentence-initial form.

Both narrowings can only remove firings. On Tier 1, Tier 2, the essays and Wikipedia the two rules together fire 0, 6, 10 and 35 times, the same set as before the change.

## Shipped

Data, tests and docs only, so a restart deploys it: the two `banned_structures.json` changes, the set and its README, `terse_*` helpers in `tests/support/fp_corpus.py`, `tests/support/test_terse_register.py`, new negatives and ReDoS cases in the BS-024 and BS-062 tests, and the bar line in `CLAUDE.md`.
