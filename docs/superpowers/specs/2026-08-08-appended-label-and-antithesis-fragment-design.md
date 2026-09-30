# BS-038 / BS-039 design: the appended significance label and the antithesis fragment

Date: 2026-08-08
Trigger: an in-the-wild reviewer report on a document that passed the 2026-08-06 checker clean.

## What was reported

A reader flagged six things in a piece of prose and asked whether they were AI tells. Running the six through the deployed checker separated them into three groups.

| Reported item | Existing coverage | Outcome |
|---|---|---|
| `What broke that version is ...` | `BS-015` wh_cleft_pronouncement | Already caught |
| `Not because the released person stopped mattering, but because the officer is where a design can reach.` | None. `BS-013` covers only the two-sentence copula flip | New rule `BS-039` |
| `Method, and why this one` (heading) | None | New rule `BS-038` |
| `Reintegration support at the moment of release from Canadian federal prison, and the officer the whole system turns on.` (dek) | None | Judgment item in `self_review.json` |
| The section symbol | Not an authorship signal | Rejected |
| Middot separators | Not an authorship signal | Rejected |

Two of the six were the same move appearing twice in one document, which is the durable form of the signal. A single rhetorical flourish is ordinary writing. The same flourish repeated is what reads as machine-made.

## BS-038 appended_wh_label

The tell is a label that names its subject and then annexes a second element promising the subject matters. In the WH form the appendix is a clause the body has not yet earned: `Method, and why this one`. The reader learns nothing from it, because a section titled `Method` was always going to defend its method.

Detection is a regex, so the rule deploys data-only.

Four guards keep it label-scoped:

1. **The appendix must end the bounded line.** The tail is capped at 30 characters and may not contain a comma, so a second clause cannot match. `The board met on Tuesday, and why it matters is another question.` fails, because no tail short enough reaches a line end.
2. **The head may not contain a subject pronoun or an auxiliary.** Each head token carries a negative lookahead over `he|she|they|we|i|you|it` plus the copula and modal set. `He explained the delay, and why it mattered.` fails on the first token.
3. **The head is capped at twelve tokens**, which keeps the match label-shaped.
4. **The line is anchored at both ends**, with optional markdown heading and bold chrome absorbed, so a mid-paragraph coordination cannot match.

## BS-039 not_but_fragment

The sentence-initial antithesis fragment. `BS-013` was written for the two-sentence copula flip (`It is not just X. It is Y.`) and returns nothing for the single-sentence fragment, which is the more common written form.

The guard here is **parallelism**. The same function word must open both limbs: `because` and `because`, `to` and `to`, `a` and `a`. That single requirement separates the rhetorical fragment from the two prose cases that otherwise look identical:

- `Not all of them agreed, but most did.` has a real subject after `Not`, and `all` does not repeat.
- `He did not go to the store, but to the park.` is an ordinary mid-sentence correlative, and `Not` is not at a sentence boundary.

## What was deliberately left to judgment

The dek form appends a reduced relative rather than a WH word: `..., and the officer the whole system turns on.` Separating that from ordinary coordination such as `Bread, and the flour that makes it` requires knowing whether the head is a verbless noun phrase, which requires a parser this server does not have.

Every lexical approximation tried during the build failed the same way. A finite-verb word list misses any verb outside the list, so `The team shipped on Friday, and the release the whole quarter depended on landed clean.` slips through. Restricting to standalone short lines does not help either, because the project's markdown convention writes each paragraph as one unbroken line, which makes a one-sentence paragraph indistinguishable from a dek.

So the appositive family is a `self_review.json` item and the gap is recorded in `caveats.json` as `labels_are_where_the_tells_hide`.

## What was rejected

The section symbol is ordinary in any document citing statute, and this one cited Canadian corrections law. Middot separators are a typography convention at least as common in human-authored web copy as in generated copy. Flagging either would repeat the smart-quote error of 2026-07-13, where a tooling artifact was mistaken for an author signal.

The bare adverb form of the antithesis fragment (`Not always, but often.`) is also unmatched. Without a shared function word it cannot be told from ordinary casual speech such as `Not bad, but okay.`, and a checker that cries wolf gets ignored.

## Verification

- 453 tests green, including the `tests/tools/*` suite.
- 0 of 16 false positives for both new rules on the genuine-human eval corpus. The corpus predates these frames, so it validates false-positive safety rather than recall. Recall is covered by the constructed unit tests in `tests/checker/test_appended_label_2026_08.py`.
- ReDoS-safe: both patterns return in under 2ms on 100k pathological tokens.
- Dogfooded on the reported text. All three mechanizable items fire; the fourth surfaces in `manual_review`.
