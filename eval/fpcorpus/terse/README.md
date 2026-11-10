# Terse-register hard-negative set

299 short lines of functional writing in 13 registers, one register per file: dosing and clinic notes, recipes and orders, listings and specs, sports results, headlines, contracts and minutes, travel and logistics, short chat and email, interface strings, figure captions, meeting notes, signs, and methods statements. Lines starting with `#` are headers.

## Why it exists

Both corpus tiers are long-form prose. Three rule rounds in a row (2026-09-29, 2026-10-30, 2026-11-09) aimed at labels, captions, cells or slogans, and each time an adversarial review found false positives the tiers could not show. On 2026-11-09 a caption rule scored zero on Tier 1, Tier 2, essays and Wikipedia, then flagged about 100 ordinary lines such as dosing instructions and box scores. This set holds that kind of writing so the next round can measure it directly.

## What it is, and what it is not

- **A standing bar, not a tier.** No regex structure may fire on any line, and the full checker in label mode may report nothing but AR-003's missing full stop. There is no rate. `tests/support/test_terse_register.py` enforces it, and `tests/support/fp_corpus.py` exposes `terse_lines()`, `terse_findings()` and `assert_terse_clear()` for a round's own candidates.
- **Written for the purpose, not excerpted.** Claude wrote the lines on 2026-11-09, and an independent review then checked each one for realism and for AI tells of its own; 18 were rewritten and 36 added. That makes it a set of legitimate constructions, not a sample of human style, so never use it to measure how human something sounds.
- **Adversarial on purpose.** Many lines are the everyday form of a shape some rule targets: "Forgot your password? Reset it here.", "Not urgent, but can you look today?", "In brief: library hours extended through exam season.", "Why the bylaw vote matters for renters", "Here's the updated draft of the lease.", "Two adults, one child.", "Looking ahead, the forecast calls for rain through Thursday.".
- **No em-dashes.** AR-002 bans them as policy, so the set leaves them out instead of testing that policy.

## The control

The numeral-contrast caption pattern rejected on 2026-11-09 is kept in the test as this set's discriminating control. It fires on 14 lines across six registers. If a change to the set stops it firing, the set has lost the shapes it exists to hold, and its zeros mean nothing.

## Adding lines

Add lines a person really writes in that register, one per line, without em-dashes. If a new line makes an existing rule fire, that is a finding: read it, decide whether the line or the rule is wrong, and record the decision in `docs/RULE-HISTORY.md`. Never weaken a line to make a rule pass.

## What it found on its first run

- `BS-062` flagged the weather line above; its date guard now spares weekdays and relative days.
- `BS-062`'s date guard was also quadratic: 9.6 seconds at the 100k-character input cap. It is now bounded to the next 200 characters of the sentence.
- `BS-024` flagged the headline "Not a recession, but close, economists say"; a trailing attribution at the end of an unpunctuated line is now declined.
