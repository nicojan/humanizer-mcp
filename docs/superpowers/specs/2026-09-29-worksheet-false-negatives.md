# Worksheet false negatives: time nouns as agents, clipped verdicts, stance closers

Date: 2026-09-29. Tests: `tests/checker/test_worksheet_tells_2026_09.py`, `tests/tools/test_guide_parts.py`. Needs a **rebuild**, because `budget_only`, the `label` content type and the guide `part` parameter are code.

## The report

A drafting session produced a B2-level student exemplar in short worksheet cells. `humanizer_check_text` returned `prohibitions_clear: true` with no lexical or structural findings. A human reviewer then flagged six phrases, in three families:

1. A time or activity noun as the agent of a survival, predation or possession verb: "Co-op hours were 9 to 5, so the Fridays survived.", "Busy season eats the Fridays.", "Billiards survives final year.", and earlier in the session "Work does not get to claim them."
2. The clipped retention verdict: "The Scouts books and the tutoring stay.", "Tutoring stays."
3. The deictic stance closer: "Seven to eight hours of sleep, and I want to keep it there."

A second pass flagged "I get my Fridays back in May" and "I have my evenings back" as a repeated shape, plus two tidy aphoristic closers ("four months is a long time to wait", "tires me out more than any lecture did"). The same session hit two tooling problems: `humanizer_get_guide(content_type="prose")` came back at about 168k characters, over the client's tool-output cap, and burstiness kept firing (stdev 5.0 to 5.6 against 6.0) on copy the caveats say to exempt.

## What shipped

| Rule | Shape | Confidence | Budget |
|---|---|---|---|
| `BS-052` `time_noun_as_agent` | three branches, each anchored at a clause, line, cell or list-item start: a weekday, weekend, part-of-day, semester or compound-season subject + survive/eat/swallow/devour/kill/steal/claim/die, followed by a determiner, an object pronoun or the sentence end; a noun subject + third-person "survives final year / the semester"; "work/school/the job does not get to claim" | low | none |
| `BS-053` `clipped_retention_verdict` | a capitalised noun-phrase subject of up to six words + stays/stay/goes + full stop | medium | 1 |
| `BS-054` `deictic_stance_closer` | a number earlier in the sentence, then "I/we want/plan/hope/'d like to keep it/them there/that way" + sentence end | low | none |
| `BS-055` `time_back_refrain` | "get/have my [time noun] back" | low | 1, budget-only |

Guards, each added because a probe fired on it: bare seasons are left out of `BS-052` ("The winter killed the roses."), as are `schedule`, `calendar` and plural `terms` ("Schedule survives restarts", "the terms claimed by the vendor"). The object guard after the verb declines `Mondays kill me`, `steal up on you`, `died away`, the passive `claimed by`, headings and compounds ("Weekend eats: five brunch spots", "Saturday claims are processed") and news ("The weekend claimed two lives"). Human subjects pass: "I barely survived the semester", "We survived another busy season". `BS-053` needs the verb to end the sentence, so "The car stays in the garage." passes. It declines pronoun, quantifier and adverb subjects in any case ("He stays.", "No one stays.", "Few stay.", "Please stay.", "So it goes.", "HE STAYS."), a name after a title ("Mr. Darcy stays."), and a determiner, modal or object pronoun before the verb ("prolonged his stay."). `remains` was dropped entirely: "Questions remain." and "The chapel remains." are ordinary prose. **Known residual:** a literal "Fine. The dog stays." still fires, because nothing short of semantics separates it from the verdict; a test pins it. `BS-054` needs a number to point back at, so "I'd like to keep it that way.", "keep it up" and the literal "the key is under the mat and I want to keep it there" pass.

Most of these guards came from an independent review of the first draft, which predicted each failure by hand. All 26 of its predictions reproduced when probed.

`budget_only` is new: `BS-055`'s single instances are dropped from `must_clear` and only the overrun is reported, carrying each instance's excerpt. One "I get my Fridays back" is ordinary writing, so flagging it would be a false positive by construction.

The attested examples also went into the rubric: the time-noun family under abstraction-as-agent, and the verdict, the stance closer and the two aphoristic closers under the performative framing beat.

## Numbers, from one run

- Recall: `BS-052` 9/9 (4 attested, 5 constructed), `BS-053` 7/7, `BS-054` 3/3, `BS-055` 2/2. Every attested phrase in the reviewed draft is now surfaced.
- Adversarial hard negatives: 0/62 (25, 26, 9 and 2 per rule). The first draft failed 27 of them.
- Tier 1 (109 sentences): 0 findings from the four rules, every file.
- Tier 2 (47,088 sentences): 0 findings, 0.0 per 10k.
- Modern control, `prose_only` view (1,582 sentences): 0 on committed text. It fires only on this spec and on the synced sibling prompt, both of which quote the examples.
- Must-be-zero sentinel, fresh for this round and built by concatenation so it never appears in prose: 0 on both tiers (`test_must_be_zero_sentinel_on_both_tiers`).
- ReDoS: every rule under 2 s on six pathological inputs of up to 360k characters (`test_redos_safe_on_pathological_input`); measured at 0.12 s for the slowest.

**Which zeros count.** A zero is reportable only if a looser version of the rule fired in the same run. For `BS-053` it did: the loose verdict pattern fires 18 times on Tier 2, and reading them is how the first draft's determiner and modal guards were found. That makes its zero partly fitted to the same firings, which is weaker than an independent measurement, and the review's modern cases ("Questions remain.") showed the Victorian corpus did not cover them. For the other three it did not. Loose controls for the time-noun agent, the stance closer and the refrain fire 0, 1 and 2 times across all three corpora combined, because Victorian novels and repository docs almost never put weekday or semester nouns in subject position. Those zeros are blind, so their precision on real human prose is **unmeasured**. With the user's agreement they ship at `confidence=low`, on the constructed evidence, with the blind controls pinned in a test (`test_the_blind_zeros_are_still_blind`) so a later corpus that makes them fire forces a re-measure. What would settle it is a modern, casual-register human corpus: personal essays or student writing.

## The two tooling fixes

**`content_type="label"` or `"notes"` on `humanizer_check_text`.** Burstiness and `segment_uniformity` are still computed and shown in `metrics`, with `length_metrics_apply: false`, but they are no longer `must_clear` items, and `burstiness_flag` and `uniformity_flag` read false so a consumer of the raw metrics sees no failure either. The 2026-08-03 caveat rejected a heuristic that would guess "this input is labels" from length. This is different, because the caller has to declare it. A test confirms the structures still fire under `label`.

**`part` on `humanizer_get_guide`.** Measured at 166,067 characters for `prose` with this round's data. It now pages as `core` (61.5k), `lexical` (32.3k), `anti_patterns` (41.6k) and `caveats` (30.9k), each with `guide_parts_remaining`. Every page stays under 75k characters, which is under a 25k-token cap even at a dense 3 characters a token, for every content type including an unknown one (whose all-profiles fallback makes `core` 73.7k). The default is still the full payload, because `test_guide_payload_keeps_existing_dimensions` pins that every consumer keeps finding every key. The server instructions now tell new callers to page.

Also fixed while answering a separate access question: a request to `/mcp/` was redirected to `http://…/mcp`, because uvicorn ignored cloudflared's `X-Forwarded-Proto`. It now runs with `proxy_headers=True, forwarded_allow_ips="*"`. That is safe because the production compose binds port 8016 to 127.0.0.1.

## Rejected or deferred

- A slimmer "major task" bundle between `get_summary` and `get_guide`. Paging solves the size limit without adding a thirteenth reader, and choosing what a slim bundle keeps would be its own round.
- Demoting burstiness automatically when the mean sentence length is short. That is the length heuristic the label caveat already rejected.
- Mechanizing the aphoristic closers. They have no lexical anchor, and the aphorism budget already sits in the rubric.
- `survives` and `remains` in `BS-053`. "Only the chapel survives." and "The chapel remains." are ordinary guidebook prose. `BS-052` covers the attested "Billiards survives final year." through its object frame.
- The verdict pair "Scouts stays, tutoring goes." and a verdict inside quotation marks. Both are left unflagged; the second is dialogue.
