# Case-study and résumé profiles, and terms of art (2026-11-09)

## Why

The content profiles covered academic, marketing, technical, general prose and creative writing. Two registers that a portfolio project writes every week had no profile, and both cost that project time on every audit:

- **Résumés.** `rule_of_three_density` fired on the Skills block, and burstiness fired on bullet fragments. A list is the format, so each audit excused both by hand. The project's notes called a server-side profile "the real fix".
- **Terms of art.** "Differentiated instruction" is a teaching term with no plainer equivalent, and it tripped the flagged word "differentiate" every time. Every suggested alternative made the sentence wrong.
- **Case studies.** The portfolio round earlier the same day put 31 reviewer flags into the self-review rubric. That guidance had no profile that a model writing a case study would be routed to.

## What changed

1. **`content_type="resume"`** (also `résumé`, `cv`) in `humanizer_check_text`. Like `label`, it keeps the length metrics in `metrics` but drops them from `must_clear`. It also skips `rule_of_three_density`. Every other layer runs, including the em-dash hard gate, the lexicon and every banned structure; a test pins that.
2. **`lexical_patterns.terms_of_art`.** Eight phrases to start with (six teaching ones, plus "differentiated diagnosis" and "differentiated cells"). A flagged word inside one is not reported in any content type. "We need to differentiate the brand." still fires. The lever is data, so a new term deploys with a restart.
3. **Two profiles**, `case_study` (aliases `case-study`, `portfolio`, `product`) and `resume` (aliases `résumé`, `cv`), in the same shape as the other five. `case_study` holds the cold-reader test, one UX decision per piece, leaving room for questions, and the shapes the portfolio reviewer flagged. `resume` holds the role-label-plus-facts summary and the voice failures the same reviewer flagged on a CV.
4. **An unknown content type now falls back to `general_prose`** in the guide and the summary, with a warning that names the valid types. It used to return every profile, and with seven profiles that put the guide's `core` page at 80,341 characters, over the 75,000-character cap that keeps it under a client's tool-output limit. `humanizer_get_content_profile` still returns every profile when asked for `all`.

## Why no corpus measurement

Every change removes findings, and none adds a detector. The terms-of-art allowlist only drops occurrences inside a listed phrase, and the `resume` type only acts when a caller declares it. The tests pin the controls: the Skills block still trips rule-of-three density as prose, and "differentiate" outside a term of art still fires.

## Deploy

**Rebuild, not restart.** `src/checker/` (`__init__.py`, `metrics.py`, `phrases.py`, `loader.py`) and `src/tools/` (`read.py`, `check.py`) changed. A restart alone would load the new profiles and the terms-of-art list, but the old code would ignore both the list and the `resume` type.
