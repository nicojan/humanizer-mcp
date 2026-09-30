# BS-040 / BS-041 design: artifact-subject carry, and the Orwell plainness pass

Date: 2026-08-10
Trigger: an audit of what a five-week design project had learned about its own copy that this server did not yet hold. The project ran this server's loop on a 39-page case study and a 21-slide pitch deck, alongside a hand-written gate of its own, and the gate kept catching things after the checker had cleared the text.

## What the audit found

Three of the project's findings had already landed here: metaphorical `carry` as BS-031 on 2026-08-06, the appended significance label as BS-038 on 2026-08-08, and the label-text metrics caveat on 2026-08-03. Four had not.

| Finding | Existing coverage | Outcome |
|---|---|---|
| An artifact noun as the subject of `carry` (`the deck carries one still`) | BS-031 covers only `carries the weight\|burden\|meaning` | New rule BS-040 |
| Stale figures of speech (`moves the needle`, `the federal purse`) | None. No Orwell content anywhere in `data/` | New rule BS-041 |
| The rest of the Orwell pass, and the jargon carve-out | Partial and unstated | `lexical_patterns.orwell`, a self-review item, protocol phase 10, a caveat |
| One-per-piece budgets defeated by per-section checking | None | Protocol wording plus a caveat |
| Whether a passage earns its page | Out of scope | Rejected |

## BS-040 artifact_subject_carry

BS-031 was built from a report that named the abstract collocation, so its object list is `weight`, `burden`, `meaning`. The form design writing actually produces is different, and the difference is the object: `each board carries its own title, rule and legend`. Six sentences of that shape, taken from the project's own working documents, were run against the deployed checker and returned `prohibitions_clear: true` with zero findings. All six now fire.

The design note on BS-031 had called the wider family unmechanizable without a parser, and for the open class that is still true. This rule takes the slice where both ends are closed lists:

- the **subject** head sits immediately before the verb and comes from an artifact/document list (deck, slide, board, page, section, rail, panel, frame, column, caption, chart, table, screen, dashboard, prototype, report, layout, card, note and their plurals)
- the **object** head comes from an informational list (title, legend, argument, tags, model, lessons, story, data, still, screenshot, claim, stakes and about sixty more), with up to two modifier tokens before it so `slide 18 carries the business model` matches on `model`

Requiring both ends is what makes it safe, because most of the artifact nouns are also load-bearing objects in the physical world. A column carries a roof, a frame carries glass, a table carries plates, a board carries a load. None of those objects is on the informational list, so none of them can match. Three exclusions were deliberate:

- **`number` was dropped** from the object list after a probe fired on `the card carries an account number on the back`, which is literal.
- **retail subjects (`store`, `shop`) were never included**, so the stocked sense in `the store carries that brand` cannot match.
- **physical-load objects were left out** for the same reason `load` and `freight` were dropped from BS-031 during its build.

Known accepted boundary: `the frame carries the image` fires, and a picture frame arguably does that literally, though the verb English uses there is `holds`.

## BS-041 stale_figure_of_speech

Orwell's first rule over a closed list: a figure the reader is used to seeing in print, which no longer produces an image and now only fills the slot where a plain statement belongs.

**This is house style, not an authorship signal**, and the file says so. Human writing reaches for these constantly, which is the entire reason the rule was worth writing in 1946. The eval corpus therefore proves nothing either way about recall, and a hit on a human text would be a true positive under the rule rather than a detector bug. It sits in `banned_structures.json` because the mechanism is a fixed phrase set, the same shape as BS-036, and at `gate: checklist` with `confidence: low` a finding is a rewrite-or-justify prompt.

Two guards keep the literal senses out, both found by probing rather than by reasoning:

1. **`raise the bar`** matches only when terminal or followed by `for`/`on`/`across`. `She raised the bar three inches and jumped again.` passes.
2. **`at the end of the day`** matches only in the filler frame: a comma, then a subject, then a copula or `comes down to`/`boils down to`/`matters`. `At the end of the day we walked back to the car.` passes.

`guardrail` was considered and rejected. In AI-safety writing it is ordinary technical vocabulary with a live meaning, and flagging it would repeat the bare-`quiet` mistake of 2026-07-13.

## The rest of the Orwell pass

Rules 1 and 2 have a mechanical slice. Rules 3, 4 and 6 do not, and pretending otherwise would cost more than the miss:

- **Rule 3 (cut every word that can go)** is the rule that does the most work in anything longer than a page, and it is pure judgment. Its padding phrases (`in order to`, `the fact that`, `in terms of`, `a number of`) are listed as guidance and deliberately **not** auto-flagged. They are frequent in ordinary human prose, so flagging them would cry wolf on every check, and Orwell's own point is that this is a fault of writing in general rather than a mark of any particular author.
- **Rule 4 (prefer the active)** is not mechanized because a be-plus-participle detector fires on every legitimate passive, and the legitimate passive is common in exactly the registers this server gets used for: method sections, regulatory writing, anything where the agent is genuinely unknown.

So the pass lands in four places, none of which needs a code change:

- `lexical_patterns.orwell`: the six rules, the long-word and padding lists, the jargon carve-out, and the instruction to re-check after trimming
- `self_review.json`: one rubric item covering the three judgment rules, surfaced in every `manual_review` list
- `foundation.application_protocol` phase 10, "Plainness pass (Orwell)", after the verification loop, with a stop condition that sends the caller back to phase 9
- `caveats.jargon_substitution_loses_meaning`

**Why phase 10 sits after phase 9 rather than before it.** The pass has to run on copy that is already clear, because a trim reflows the rhythm, and it produces a re-check rather than replacing one: cutting words lowers sentence-length variance and can undo the burstiness work. Ordering it before verification would mean checking the text and then changing it.

### The jargon carve-out

Rule 5 reads "never use a jargon word if you can think of an everyday English equivalent", and the condition fails more often than the rule's popularity suggests. `Statutory release` is not `automatic release`. `Protected B` is not `confidential`. A subpoena is not a request. Substituting the everyday word does not simplify the sentence, it changes what the sentence claims, which puts the rule in direct conflict with AR-001.

The resolution, which the source project had to work out by hand across eight corrections-domain terms: define the term in plain words at first use, then use the term plainly, and never substitute. The test is whether an everyday word means the same thing.

## Document budgets and per-section checking

Several rules budget a shape at one instance per piece: BS-011 and BS-039 for the antithesis, BS-038 and its rubric sibling for the appended label, the aphorism in the performative-framing item. All of them rest on repetition being the signal.

`humanizer_check_text` is stateless and counts only within the text it is handed, and the recommended workflow makes the gap likely rather than theoretical: a long document is written and checked section by section, so each call sees one instance and reports a single finding the writer can reasonably justify. On the source project's 39-page case study the appended label had been justified four separate times, once per section, and the repetition was only visible when the sections were read together.

Fixed in the protocol rather than in the checker: the last run of phase 9 is on the assembled document. The mechanical version, a document-level count of structures tagged with a budget, was **scoped out rather than rejected**, and `caveats.per_section_checks_miss_document_budgets` records that.

## What was rejected

**"Does the passage earn its page"** was the source project's own strongest editing rule: a passage earns its place if it changes a design decision or shows the reasoning behind one, and production trivia does not, however hard-won. It is out of scope here. This server rules on how prose reads. Whether a passage deserves its space is an editorial judgment about content, and the only thing the server could do with the rule is restate it as a rubric line it has no way to check. It belongs in the project's gate, where it lives.

**A content profile for the case study or portfolio register** was also left out. The argument for it is real (that register is first-person and evidence-led, has near-zero tolerance for the aphoristic closer, and has a structural excessive-coherence risk because every section wants to resolve), but there is one document to test it against, and a profile tuned on a single sample is a guess. Revisit when a second case study exists.

## Verification

- 524 tests green, including `tests/tools/*`. 71 of them are new, in `tests/checker/test_orwell_and_carry_2026_08.py`.
- 0 of 16 false positives on the genuine-human eval corpus for both new rules. Across every structure the corpus now returns one finding in total, a pre-existing BS-011 on `human_marketing_01.txt`, unchanged by this round.
- 0 of 19 on constructed literal-carry probes for BS-040, and 0 of 10 on literal-sense probes for BS-041.
- ReDoS-safe: 107ms for BS-040 and 27ms for BS-041 on 440k pathological characters.
- Dogfooded on the six reported sentences plus four stale figures: all ten fire, and every one of them passed the previous build clean.
- Data-only. Every rule here deploys by `git push` plus `docker restart mcp-humanizer`, with no image rebuild.
