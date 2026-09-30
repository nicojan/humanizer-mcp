# Copula avoidance and the September 2026 survey round

Date: 2026-09-17
Status: accepted

## Trigger

A survey of current AI-writing tells, both user-identified (Wikipedia's editor-maintained "Signs of AI writing", the tropes.fyi community list, the slop-sense pattern set, practitioner posts) and research-identified (the ACL-anthology corpus study arXiv:2605.19936, the biomedical excess-vocabulary study in Science Advances, the civil-engineering replication arXiv:2602.03864), cross-checked against the 42 rules already deployed.

Every candidate below was probed against the live checker before being written up. The lexical cross-check found twenty-five of the surveyed words already flagged: delve, tapestry, underscore, meticulous, intricate, garner, interplay, bolster, foster, showcase, enhance, utilize, comprehensive, crucial, notably, pivotal, valuable, vibrant, boast, harness, illuminate, navigate, robust, groundbreaking and testament. So the vocabulary half of the survey was mostly covered already. The structural half was not.

## The headline gap: copula avoidance

Four independent sources name it and the checker had no coverage at all. The model will not write `is`; it reaches for `serves as`, `stands as`, `functions as`, `operates as`, `represents`, `constitutes`, `embodies`, `comprises`, `encompasses`, `resides`, `boasts`, `features`. slop-sense estimates the substitute carries meaning the copula would not in roughly one case in ten. `The report serves as a guide.` and `Gallery 825 stands as the exhibition space.` both returned nothing from the deployed build.

The verb list does not ship whole, because most of its members have strong literal senses. A rejection probe put eight sentences using the other verbs through a bare word match and **all eight were legitimate**: `The capacitor functions as a filter.` `The clinic operates as a charity registered in Ontario.` `The region comprises four districts.` `The programme encompasses four regions.` `That constitutes a breach of the agreement.` `He resides in Ottawa.` `The Mona Lisa resides in the Louvre.` `The board comprises seven members.` Flagging those is the `flow_over_surface_features` trap. So the family splits into two narrow rules and one documented rejection.

### BS-043 `copula_avoidance`

`serves as` and `stands as` followed by a determiner. These two are the pair with no competing technical sense, unlike `functions as` (engineering) and `operates as` (legal and organisational), which are dropped for the same reason `load` and `freight` were dropped from `BS-031`.

The FP guard is a **role-object exclusion with a three-token window**: a person holding an office is ordinary English (`She serves as chair of the committee.`, `He served as interim director for a year.`, `She stood as the Labour candidate in 2019.`). The window matters, because the role word is often not adjacent to the determiner; a lookahead checking only the next token let `the Labour candidate` through. The electoral sense of `stands as` is covered by the same list.

Verified: recall 7/7, FP 0/14, 0/16 on the human eval corpus, ReDoS-safe (0ms on 480k pathological characters).

### BS-044 `significance_predicate`

`represents`, `marks`, `embodies`, `exemplifies` followed by a determiner and an evaluative abstract noun from a closed list (`shift`, `turning point`, `milestone`, `departure`, `testament`, `commitment`, `culmination`, `cornerstone`, `paradigm`…). This is the other half of the copula dodge, where the substitute verb also inflates the claim.

Both ends are closed, which is what keeps the literal senses clean: `The graph represents the data from three sites.`, `The lawyer represents the defendant.`, `The symbol represents hydrogen.`, `The line marks the boundary between the two lots.`, `The union represents four thousand workers.` all pass, because no concrete object is on the list. Overlaps `BS-004` `significance_puffery` at the edges; `BS-004` matches four fixed strings, this matches the frame.

Verified: recall 5/5, FP 0/8, 0/16 on the human eval corpus.

## The rest of the round

`BS-045` `signposted_conclusion`. `In conclusion`, `To sum up`, `In summary`, `To conclude`, `In closing`, `All in all`, at a sentence or line boundary. Legitimate in academic and report writing, hence `checklist`. Recall 4/4, FP 0/3.

`BS-046` `staccato_negation_triple`. `Not a bug. Not a feature. A fundamental design flaw.` Two consecutive `Not`-initial fragments. Distinct from `BS-013` (two-sentence copula flip) and `BS-039` (single-sentence `Not because X, but because Y`), which are both two-limb. **The FP guard is a required determiner** (`Not a|an|the|just`), which is what excludes ordinary human emphasis: `Not now. Not ever.` and `Not bad. Not great.` both pass, because the fragments are adverbial rather than nominal. Recall 3/3, FP 0/5.

`BS-047` `analogy_invitation`. `Think of it as a …` / `Think of it like a …` at a sentence boundary. Recall 2/2, FP 0/3; quoted dialogue never matches because the opening quotation mark breaks the boundary anchor.

`BS-048` `structure_announcement`. `Let's break this down`, `Let's unpack`, `Let's dive into`, `Let's walk through`. These announce procedure rather than stance, which is what separates them from the 2026-07-25 rejection of `Let's be honest`. **`Let's explore` was cut from the list during the build** as too close to ordinary collaborative writing. Recall 4/4, FP 0/5.

`BS-027` extension. `Imagine a world where` / `Picture a world where`. The rule already held `In a world where`; the imperative variant is the more common one now and was passing clean.

`BS-035` extension. `As we have seen`, `As we explored above`, `As we established earlier`, `As I have covered`. The rule held only the `mentioned/noted/discussed` set. The new alternation **requires a following comma or semicolon**, a guard added after a probe fired on `As we have seen the results, we can decide.`, where the verb takes an object and the clause is not a cross-reference at all.

## Lexical additions

From the promotional and excess-vocabulary lists, restricted to evaluative words rather than neutral structural verbs: adjectives `profound` and `renowned`; the verb `nestle`; the multi-word nouns `diverse array` and `natural beauty`.

## Rejected, with reasons

- **The rest of the copula verb list** (`functions as`, `operates as`, `comprises`, `encompasses`, `constitutes`, `resides`, `features`). 8/8 of the probe sentences were legitimate uses. These are neutral structural verbs whose tell is redundancy against `is`, which is a judgment the checker cannot make.
- **Bare `diverse`, `align with`, `notable`, `superior`.** Ordinary high-frequency words. `diverse array` ships instead, the same scoping that made `hidden gem` work where bare `gem` would not.
- **Formatting and markup tells** (curly quotes, emoji bullets, bold-first bullets, title-case headings, and the model-specific leakage strings `contentReference`, `oaicite`, `[cite: 1]`, `grok_render_citation_card_json`). Tooling artifacts, not author signals. The leakage strings are real provenance evidence but they are not style, and this server checks prose. Consistent with the smart-quote rejection of 2026-07-13 and the middot rejection of 2026-08-08.
- **Bare `quietly`.** Named again by two sources in this survey. Rejected 2026-07-13, upheld 2026-08-06 by scoping to the collocation in `BS-033`. The rejection stands for the third time.
- **Definite-article omission** (`rain in teeth`, `Coffee and cocoa leaned wild`). A real artifact of poetry generation, but a detector for it would fire on every headline, label and list item in ordinary copy, which collides with `metrics_do_not_apply_to_label_text`.
- **`Here's the thing`.** Named again. Still rejected: the sibling `PROMPT.md` recommends it as a human transition, so flagging it would make the pair contradict each other.
- **Anaphora abuse** (three or more consecutive sentences opening on the same word). Attested, and a genuine generalization of `BS-009`, which handles `This`/`These`/`It` only. **Scoped out rather than rejected**: it needs a detector in `src/checker/structures.py` and therefore a rebuild rather than a restart, and the FP surface is wide, because `The X … The Y … The Z …` is ordinary paragraph construction. Recorded for a later round.
- **Invented concept labels** (`the supervision paradox`, `the acceleration trap`). Attested and genuinely machine-flavoured, but there is no signature: the shape is a determiner, a noun and an abstract noun, which is also how real coined terms look.

## Deployment

Data-only. Six new `banned_structures` regexes plus two pattern extensions, all auto-wired by `loader.load_regex_structures`, plus `anti_patterns.json` and `lexical_patterns.json` edits. **Restart, no rebuild.** The sibling paste-prompt repo is synced in the same round.

## Tests

`tests/checker/test_tells_2026_09_survey.py`.
