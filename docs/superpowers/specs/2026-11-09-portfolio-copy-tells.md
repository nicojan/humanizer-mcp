# Portfolio-copy tells (2026-11-09)

## Trigger

Between 11 October and 5 November 2026, Nico rewrote the copy on nicojan.com across about twenty Claude Code sessions. In those sessions he called 31 lines of Claude-written copy "AI-coded", empty or unclear to a first-time reader. Every line had already gone through the humanizer check→fix loop. The lines came from those sessions' transcripts, the copy notes they saved, and two revision spreadsheets (the November one is still blank). Partial quotes were completed from the site's git history.

On 9 November all 31 went through `run_checks` again, with a control line in the same run that did fire (a hard violation and a flagged term). All 31 returned `prohibitions_clear: true` with no structural finding. One caption tripped `AR-003` for a missing full stop, and two short ones tripped burstiness, which `metrics_do_not_apply_to_label_text` already says to ignore. None of those is why he flagged them.

## The seven shapes

1. A cause-to-benefit "so" tail: "Quip updates itself, so a fix reached people within a day of shipping."
2. A maxim in which an idea or an object does the acting: "the answer usually costs you the design you arrived with", "the only thing I do that asks me to stand still".
3. Backstory told in order: "Ten years of teaching neurodivergent and multilingual learners came first, and so did the habit of watching where people get stuck."
4. Numeral-contrast captions and slogans that leave nothing to picture: "One count, four moments", "Three sizes, all the same height."
5. A flattering or modest aside about the writer: "keep the Figma files behind them tidy", "People I've never met use it".
6. How it works, in the app's own words, in place of what the user gets: "Show them in every space and they stay at the top of the sidebar, with one sign-in and one unread count, while the rest of the list changes."
7. Vague counts, run-in labels and release history: "a dozen or so", "The worst bug:", "first release 13 July 2026".

Some of his other notes were about what a portfolio should contain (sections that aren't UX, blaming outside circumstances, giving away too much). Those are content strategy, not prose texture, and they stay in the site's own copy rules.

## Probes

Five candidates were written as patterns and run over Tier 1 (109 sentences), Tier 2 (47,088), 246 pre-2022 essays and 201 pre-2022 Wikipedia articles, each with a looser control in the same run.

| Candidate | Recall on the 31 | Corpora | Control | Outcome |
|---|---|---|---|---|
| Numeral-contrast caption | 2 of 2 attested, 10 of 10 constructed | 0 on all four | 10, 12 and 42 on the large three | Rejected after review |
| "The job was" plus a gerund | 1 | 1 on the essays | 0 | Rejected: the essay firing ("The hard part was predicting how tough...") is ordinary prose, and literal job descriptions share the frame |
| "and so did the habit of" | 2 of 2 constructed | 0 | 6 on Tier 2 | Rejected: "Prices rose, and so did the practice of haggling." fires |
| "the only thing I do that asks me to" | 1 | 0 | 0 | Rejected: a blind zero, and "the only thing I do that forces me to get out" is casual human prose |
| Cause-to-benefit "so" tail | 2 | 0 | 0 | Rejected: a blind zero on a frame that is everywhere in plain writing |

The caption rule was the only one with a reportable zero. Its pattern needed the number pair to be the whole sentence or line, and the declined control firings were all inventories, board compositions and box scores inside longer sentences. ReDoS timings stayed under 0.02 seconds on 200k-character inputs.

## Why the caption rule was rejected

An independent reviewer built about 200 modern lines in registers the corpora cannot show. About 100 legitimate ones fired: dosing ("Two tablets, every four hours."), recipes and orders ("One coffee, no sugar."), listings ("Three bedrooms, one bath."), box scores ("Three goals, one assist."), headlines ("Two killed, one injured in crash."), travel and chat ("Two adults, one child."), and a lowercase number at the start of a hard-wrapped line, because the loader compiles every pattern with `re.IGNORECASE`. Six tightenings were proposed, but some lines cannot be separated from the tell: "Two adults, one child." and "Two hands, one heart." are the same construction. A detector that flags discharge instructions to catch a tagline breaks the false-positive discipline, so the shape is a rubric item. The corpus zero was real and still misleading, because none of the four corpora holds terse labels. This is the third round running in which the review found what the corpora could not.

## What shipped (data only)

- `self_review.json`: three new items (the "so" tail; backstory order and self-portrait flourish; a cold-reader test for product, portfolio and case-study copy), and attested examples added to abstraction-as-agent and performative framing, the second now holding the numeric caption.
- `anti_patterns.json`: `AP-069`, the caption with a plain rewrite, marked as not mechanized.
- `caveats.json`: `reviewed_copy_passes_the_checker`, so a calling model knows a clean report on product copy says little until the rubric has been read.
- `tests/checker/test_portfolio_tells_2026_11.py`: pins the rubric text, the caveat and the rejection, and keeps 25 of the reviewer's legitimate terse lines as a standing hard-negative set that no structural rule may flag.

No code changed, so a restart deploys it.
