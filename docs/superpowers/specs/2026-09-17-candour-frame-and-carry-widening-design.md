# Conjoined candour frame, abstract-subject `carry`, and a second negative on the appositive label

Date: 2026-09-17
Status: accepted

## Trigger

An in-the-wild report naming three shapes as dead giveaways of generated text: metaphorical `carry`, the appended candour beat (`..., and I'm not going to pretend`), and the appositive label (`X, and the Y that Zs`). Two of the three were already partly covered here; one had been rejected on the record. This round establishes what each is worth against evidence rather than against intuition.

## Coverage before this round

Probed against the deployed checker before any change:

| Probe | Result |
|---|---|
| `I won't pretend it was easy. But it worked.` | BS-017 fires |
| `The redesign took nine months, and I'm not going to pretend otherwise.` | nothing |
| `Method, and why this one.` | BS-038 fires |
| `Reintegration support at the moment of release, and the officer the whole system turns on.` | nothing |
| `The rebuild carries the argument for the whole quarter.` | nothing |

So: the candour frame is covered only in its two-sentence form, the appositive label not at all, and metaphorical `carry` only for fixed collocations (BS-031) and artifact subjects (BS-040).

## Decision 1: BS-042 `conjoined_candour_disclaimer` (ships)

The first-person candour beat appended to the clause it follows: `The redesign took nine months, and I'm not going to pretend that was the plan.` A performed admission that costs the writer nothing, placed where it reads as earned honesty.

BS-017 does not reach it. That rule matches a disclaiming sentence followed by a short `But ...` reversal, and requires both an auxiliary from a fixed list (which excludes `am not going to`) and a sentence boundary. The conjoined form has neither.

**Scope: the conjoined form only.** A comma plus `and`/`but` must precede the frame. This is the guard that answers the 2026-07-25 rejection of `Here's the thing` and `Let's be honest` as register-dependent traps. Sentence-initial `I'm not going to pretend I understand the tax code.` is an ordinary hedge and stays unflagged; the tell is the *appending*, where the beat attaches to a finished statement to add a note of candour rather than to qualify a claim. That distinction is mechanizable, and the bare phrase is not.

Method: regex, auto-wired via `loader.load_regex_structures`. Gate `checklist` (`must_clear`), never hard. `AP-055` as `source_examples`.

Verified: recall 7/7 on constructed positives (straight and curly apostrophes, `and`/`but`, `am`/`'m`/`gonna`/`won't`), 0/10 on constructed negatives, 0/16 on the human eval corpus, ReDoS-safe (0ms on 360k pathological characters).

## Decision 2: BS-040 subject-list extension (ships)

`The rebuild carries the argument` fails only because `rebuild` is not on BS-040's subject list; `argument` is already on its object list. The fix is to extend the subject alternation with abstract process and project nouns: rebuild, redesign, rollout, launch, migration, refactor, overhaul, revamp, project, programme, program, initiative, effort, process, method, approach, decision, change, shift, pivot, experiment, pilot, study, analysis, argument, review.

Both ends stay closed lists, which is the discipline that keeps BS-040's homographs literal. The boundary this round had to hold is that `carries risk`, `carries a cost`, `carries weight`, `carries a penalty` and `carries consequences` are ordinary business and legal register. They stay clean because no such object is on the object list, and nothing was added to it.

Verified: 5/5 on constructed positives, 0/15 on negatives (including the idiomatic-register set and BS-040's existing literal probes), 0/16 on the human eval corpus.

The open class (any abstract noun as subject of `carry`) remains the `self_review` abstraction-as-agent item, which already names `carry` as its hardest instance.

## Decision 3: the appositive label does NOT ship (second recorded negative)

`Reintegration support at the moment of release, and the officer the whole system turns on.` The sibling of BS-038 that appends a reduced relative instead of a WH clause. Rejected on 2026-08-08 in `caveats.labels_are_where_the_tells_hide` as needing a parser. This round re-tested it and the rejection holds, now with numbers.

**Attempt A, loose pattern, BS-038's guards, no verb handling.** 3/3 recall, **10/10 false positives** on ordinary coordination with a non-pronoun subject (`The baker bought bread, and the flour that makes it.`). The 0/16 on the human corpus is meaningless here: the corpus simply lacks the shape, so the zero measures absence rather than discrimination.

**Attempt B, a density gate (fire only at >=2 per document).** Rejected on reasoning; never run. A density gate works when individual instances are legitimate and the clustering is the signal, which is why `rule_of_three_density` and `segment_uniformity` work. Per-instance precision here is zero, so a threshold of two only means two ordinary sentences trip it.

**Attempt C, a finite-verb blocklist on the head** (`-ed` forms plus a common irregular and 3sg list), the approach the August note reports as failed. 4/5 recall, 1/14 FP. Better than the note implied, and still disqualifying:

- The miss is `The revised release policy, and the parole officer at its centre`. `revised` matches the `-ed` guard. Past-participle *modifiers* (revised, updated, proposed, rebuilt, extended) are common in exactly the label register this rule targets, so the guard eats the target.
- The FP is `The vendor ships on Tuesday, and the invoice follows`. `ships` is not in the 3sg list, and that list is open by nature.

Precision and recall trade directly against each other through a part-of-speech boundary a regex cannot see. The standing bar in this repo is 0 FP on constructed literal probes (BS-040 reported 0/19); 1/14 does not meet it.

So the shape stays judgment-only. The caveat `labels_are_where_the_tells_hide` is updated to record attempt C with its numbers, and `self_review` item 8 is sharpened with the attested example forms and a stated budget of one per document. The budget matters because the August report's own finding was that the durable signal is the repeated shape, not any single instance, and `per_section_checks_miss_document_budgets` records that a section-by-section walk cannot count that.

## Rejected without a probe

Extending BS-042 to the bare sentence-initial `I'm not going to pretend ...`. It is ordinary first-person speech and flagging it is the `flow_over_surface_features` low-ceiling trap, the same reasoning that killed the bare `quiet` flag on 2026-07-13 and `Here's the thing` on 2026-07-25.

## Deployment

Data-only. Both shipped changes are `banned_structures.json` regexes auto-wired by `loader.load_regex_structures`, plus `anti_patterns.json`, `caveats.json` and `self_review.json` edits. **Restart, no rebuild.** The sibling paste-prompt repo `humanize-text-prompt` is synced in the same round.

## Tests

`tests/checker/test_tells_2026_09.py` holds positives, constructed negatives and corpus assertions for BS-042 and the BS-040 extension, and a regression pinning that the appositive form stays unflagged so a later round does not reintroduce it by accident.
