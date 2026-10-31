# Research round: academic tells, measured against a modern sample

Date: 2026-10-30. Tests: `tests/checker/test_research_tells_2026_10.py`. **Data only, so restart, not rebuild:** every new rule is a `regex` entry auto-wired by `loader.load_regex_structures`, and `budget_only` has been in the image since 2026-09-29. New dev tooling: `eval/fpcorpus/fetch_modern_probe.py`.

## The question

A literature survey of 2024 to 2026 work on how LLM prose differs from human prose, run as two parallel searches (lexical and stylometric findings; rhetorical and structural findings), to find rules this server does not have yet. The sources that produced candidates:

- Reinhart et al., "Do LLMs write like humans? Variation in grammatical and rhetorical styles", PNAS 2025: Biber register features across instruction-tuned and base models.
- Russell, Karpinska and Iyyer, "People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text", ACL 2025: the clues expert annotators cite.
- Chakrabarty, Laban and Wu, "Can AI writing be salvaged?", CHI 2025: 8,035 professional edits to LLM paragraphs, by category.
- Paech, Roush, Goldfeder and Shwartz-Ziv, "Antislop", arXiv 2510.15061 (2025): over-represented words and trigrams across 67 models.
- Sun et al., "Idiosyncrasies in Large Language Models", ICML 2025.
- Graphite, "AI Tells" (September 2026): phrase ratios for nine current models against 10k pre-ChatGPT articles. An industry study, not peer-reviewed; treated as a lead to measure, never as evidence on its own.
- Wikipedia:Signs of AI writing, read as raw wikitext on 2026-10-30.
- Also used for rejections or corrections: Herbold et al. 2023, Kendro et al. 2025, Dentella et al. 2025, Jiang and Hyland 2025, Bakhshi 2026, Jakesch et al. PNAS 2023, Shaib et al. 2024 and 2025, Kobak et al. 2025.

## What changed the round: a default-model sample

Every published ratio in that list compares some model with some human corpus, and most of the models are not the ones people use now. So before writing any rule, two subagents (Claude Sonnet and Claude Haiku) were each given the same 16 bare prompts across 16 genres (short stories, blog posts, an opinion essay, a feature, a news story, product copy, a cover letter, an explainer, a personal essay, an About page, a history article, a LinkedIn post) and told to write in their unmodified default style with no style guidance and no MCP tools. That gave 32 pieces, 943 sentences.

**The existing checker passes most of them.** 21 of the 32 came back with two findings or fewer, none had a hard violation, and most of the findings were comma splices and run-ons rather than tells. Reading the clean ones, the tells a reader would still notice were concentrated in the closers: a balanced maxim ("Gardening is as much about patience as technique."), an upbeat forecast, an announcement that something matters ("Knowing which type you have matters more than most beginners realize."), a reassurance opener ("If this sounds familiar, take heart."). That is now `caveats.default_model_prose_mostly_passes`.

**The sample also killed the two candidates with the strongest published numbers** (see Rejected).

## What shipped

| Rule | Shape | Confidence | Budget |
|---|---|---|---|
| `BS-056` `graded_contrast_like` | "less like X ... more like Y" inside one clause | medium | none |
| `BS-057` `graded_contrast_about` | "less about X ... more about Y" inside one clause | low | 1, budget-only |
| `BS-058` `chatbot_residue` | "Certainly!/Absolutely! Here is a [text artifact]", "As an AI language model, I", "as of my last knowledge cutoff", "Here's a polished/rewritten version", "Would you like me to expand on / elaborate on / adjust the tone" | high | none |
| `BS-059` `fiction_stock_phrase` | closed list of Antislop collocations in third-person narration, plus the default names Elara and Kael | medium | none |
| `BS-060` `abstract_emotion_frame` | "a/an (uneasy) mix/blend of [emotion] and [emotion]", "the weight of the unspoken" | medium | none |
| `BS-061` `corrective_framing_disclaimer` | "should be treated as X rather than as [evidentiary adjective] Y", "not widely documented", "based on the provided sources", "in the provided context" | low | none |
| `BS-062` `optimistic_future_closer` | "As the [field/industry/technology...] continues to evolve,", "Looking ahead," without a date or number, "One thing is clear:", "the future ... looks bright", **last paragraph only** | medium | none |
| `BS-063` `importance_flag` | "This distinction matters because", "matters more than most X realize", heading "Why this matters" | low | none |
| `BS-064` `as_much_about_aphorism` | "X is ('s) as much about A as B", **last paragraph only** | low | none |
| `BS-030` extended | "If this/that sounds familiar (to you), take heart / you're not alone / don't worry / rest assured", "Sound familiar? You're not alone." | low (unchanged) | none |

Plus four lexicon terms at `severity=low` (`camaraderie`, `unease`, `palpable`, `unspoken`), four anti-patterns (`AP-065`..`AP-068`), three `self_review` items (over-explained subtext; reader contact in essay registers; recognisable defaults: rotating speech tags, bold-label bullets, emoji headings, stock names) and one caveat.

**Guards, each added because a hard negative fired on the first draft:**

- `BS-058` lost "I hope this helps", "You're absolutely right", "I'd be happy to help", "Let me know if you'd like me to", "Great question" and a bare "Sure! I'll ...". Every one is ordinary courtesy in human email. What is left is meta-talk that only makes sense addressed to the person who requested the text.
- `BS-061` needs the second "as" ("treated as X rather than **as** Y"), because "It should be read as a whole rather than in parts." is an ordinary instruction. "does not establish that" was never added: it is standard legal and academic phrasing.
- The `BS-030` extension needs the reassurance continuation, because "If this sounds familiar, it's because I wrote about it last week." is a legitimate callback.
- `BS-063` needs the third-person "matters", so Paul Graham's "it may matter more than outsiders think" passes.
- `BS-062` and `BS-064` end in a lookahead that walks to the end of the text and fails at the next blank line followed by content, so the same phrase in the body passes. A one-paragraph input is its own last paragraph, which is the right answer for the final assembled check and the wrong one for a section-by-section walk; `per_section_checks_miss_document_budgets` already tells callers to run the last check on the assembled document.
- `BS-059` left out "took a deep breath" (in 44.8 percent of Antislop's model lists, but ordinary in human fiction) and "something else entirely" (fires on Paul Graham's non-fiction).
- `BS-060` left out bare "a sense of" and "felt a sense of" (they fire in every human corpus: "feel a sense of urgency", "felt a sense of injury").
- `BS-058` also needs "As an AI" to take a comma and then "I": running the new rules over the sibling prompt during the sync caught the first draft firing on "They read as an AI tell".
- No pattern uses a scoped inline flag group (a case or multiline modifier applied to part of a pattern), so the browser port can translate each one to a plain JS `RegExp`; a test pins this.

## The independent review

An adversarial reviewer, given only the patterns, the tests and this spec, traced the regexes by hand against registers the corpora do not contain: client email, Slack, legal and academic prose, news, film criticism, CRLF documents. It predicted 9 high-priority false positives and a scoping bug from hand traces. The patterns were narrowed and rewritten together rather than one at a time, so each sentence was not re-run against the pre-review pattern; every one is now a hard negative in the test file, and the CRLF and quadratic-time findings were confirmed by measurement. The narrowings:

- `BS-058`: "Sure! / Of course! Here's the Zoom link" (dropped "sure" and "of course"; "Certainly!" and "Absolutely!" now need an article and a text-artifact noun after "Here is"); "Here's the updated draft of the lease" (dropped "updated", "revised", "edited"); "Would you like me to make any changes before it goes to print?" (dropped the "make changes" branch); "As an AI researcher, I've watched..." (needs "As an AI [model/assistant], I").
- `BS-061`: "The provision should be read as a limitation rather than as a grant of authority" and "interpreted as exploratory rather than as confirmatory" (the Y side now needs an evidentiary adjective); "Based on the available information, police believe" and "the available sources before 1650" (only "provided" survives).
- `BS-062`: Windows line endings defeated the paragraph test entirely, because the first lookahead allowed only spaces and tabs between the two newlines (fixed: carriage returns count as blank-line whitespace). "It remains to be seen whether the Senate will take up the bill" and "Only time will tell" are neutral wire-story and review endings, so both were dropped. "As the plant continues to grow, move it to a larger pot" (the subject is now a short list of abstract nouns). "Looking ahead, phase two opens on 3 March" (no digit or month in the sentence).
- `BS-059`: "Pauline Kael", "I woke with my heart pounding in my chest" (third-person possessives only), "my voice was barely audible on calls", "thick with the smell of tear gas", "a profound sense of loss" (condolences) and "I couldn't shake the feeling I'd left the stove on" (all four phrases removed).
- `BS-063`: "The order matters here: auth middleware must run first" (the "here" branch is gone).
- `BS-064`: "The film is as much about the city as it is about the people who leave it", the stock review sentence (now last-paragraph only).
- **Accepted, with the boundary written into the entry:** reaction-story "a mix of relief and anger" (`BS-060`, evidence is from fiction), "Your credit score matters more than you think" (`BS-063`), "It plays less like a sequel and more like a remake" (`BS-056`, review register, 82 to 105 times the human rate), "This API behaviour is not widely documented" (`BS-061`) and "If this sounds familiar, don't worry: it's a known issue" (`BS-030`). Known recall gaps, also recorded: a sign-off after the closer hides it from `BS-062`, and text whose paragraphs are separated by single newlines reads as one paragraph.
- **ReDoS, found by the review and confirmed:** with many candidate phrases and no paragraph break after them, the first lookahead was quadratic (0.6 seconds at the 100k-character input cap); the narrowed per-character version was worse (3.3 seconds). The shipped lookahead consumes each line as one possessive run (`[^\n]*+`, Python 3.11 and later; the image runs 3.12) and takes 0.04 seconds on the same input. The three adversarial inputs are now in the test file.
- **Cheap recall added:** "It's as much about", "matters more than you'd think", "an uneasy mix of hope and fear", "she said, barely above a whisper", "Certainly, here's a revised version", "as of my last knowledge cutoff", "Sound familiar? You're not alone", "If this sounds familiar to you". The review's sentence-start note (two spaces, or a closing quote, before the sentence) is handled by a shared sentence-start group in `BS-063`.

The measurement below was re-run after the narrowing: same zeros, same 6 default-sample hits, so the review cost no measured recall.

## Numbers, from one run

Five text sets in one invocation. `T1` is `eval/corpus/human`. `T2` is the Tier 2 long-form corpus. `ESSAYS` is every Paul Graham essay linked from his index (246 pages, 34,548 sentences). `WIKI2021` is 201 Wikipedia Featured Articles, each at its last revision before 2022 (39,891 sentences). `AIGEN` is the 32-piece default sample above (943 sentences). ESSAYS and WIKI2021 are rebuilt by `python -m eval.fpcorpus.fetch_modern_probe` and are gitignored. They are a probe set, deliberately **not** a third tier, for the reasons the 2026-09-18 `BS-011` round recorded. The AI sample is not committed.

| Rule | T1 | T2 | ESSAYS | WIKI2021 | AIGEN |
|---|---|---|---|---|---|
| `BS-056` | 0 | 0 | 0 | 0 | 1 |
| `BS-057` (single instances) | 0 | 0 | 3 (0.9 per 10k) | 0 | 0 |
| `BS-058` | 0 | 0 | 0 | 0 | 0 |
| `BS-059` | 0 | 0 | 0 | 0 | 0 |
| `BS-060` | 0 | 0 | 0 | 0 | 0 |
| `BS-061` | 0 | 0 | 0 | 0 | 0 |
| `BS-062` | 0 | 0 | 0 | 0 | 0 |
| `BS-063` | 0 | 0 | 0 | 0 | 2 |
| `BS-064` | 0 | 0 | 0 | 0 | 1 |
| `BS-030` extension | 0 | 0 | 0 | 0 | 1 |

**0 per-instance firings across 121,527 human sentences** on the three large corpora, so 0.0 per 10k on Tier 2 and inside the bar on every set. The three `BS-057` single instances on ESSAYS were all read and are all legitimate human prose ("the study of ancient texts became less about ancientness and more about texts"). That is why the "about" form is budget-only and reports nothing until it repeats; no ESSAYS document repeats it.

**Controls in the same run**, each a loose version of a frame that must fire for the scoped zero to mean anything: `less ... more` 17 / 34 / 14 on T2 / ESSAYS / WIKI2021; `voice` 273 / 8 / 105; `rather than` 40 / 169 / 121; `continues to` 11 / 44 / 41; `matters` 86 / 91 / 37; `as much` 168 / 129 / 47; `mix of` 12 / 10 / 27; `sounds` 53 / 113 / 90. **Must-be-zero sentinel** `whelkbrine obquaver`: 0 everywhere (pick a fresh one next round, since this file now contains it).

**Recall.** 6 hits in 5 of the 32 default pieces, plus 44/44 constructed positives and 0/76 hard negatives in the test file (5 and 3 more for the `BS-030` extension). The default sample is small and comes from one model family; most of the new rules target tells of other models (`BS-058`, `BS-059`, `BS-061` from GPT and Gemini-era sources), and their zero on AIGEN is a recall measurement on Claude, not evidence against them. **`BS-058` through `BS-062` therefore rest on published evidence plus constructed positives.** `BS-063` and `BS-064` rest on the sample plus Graphite, and ship at `confidence=low` for that reason.

**Lexicon, per term**, as `lexicon_rate_is_not_a_detector_rate` requires: `camaraderie` 0 / 0 / 0 on T2 / ESSAYS / WIKI2021; `unease` 0 / 0 / 1; `palpable` 8 / 2 / 0 (1.7 per 10k on T2); `unspoken` 1 / 1 / 0. All inside the bar. `amidst` (10 / 0 / 6, and 0 in AIGEN) was not added.

**ReDoS.** Ten pathological inputs of 95k characters or more (the tool caps input at 100k), all nine rules plus `BS-030`, each under the 2-second ceiling in the test file; see the review section for the lookahead that needed it.

## Data corrected

The survey found four places where the data contradicted the literature or this server's own detectors:

1. `lexical_patterns.vocabulary_diversity` said human text has a higher type-token ratio. Herbold et al. (2023, already cited in this repo) found ChatGPT essays **more** lexically diverse, and Kendro et al. (2025) found newer models more diverse again. The direction depends on the model, so the entry now says not to target it.
2. `structural_patterns` said "AI text uses passive voice at a steady rate". GPT-4o uses the agentless passive at about half the human rate (Reinhart et al.). The guidance now says not to strip passives in order to sound human.
3. `human_adverbs_to_reintroduce` recommended "quietly" (the `BS-033` / `AP-046` tic), "actually" (counted by `credibility_insistence`) and "honestly" (the `AP-045` false-candour opener). All three are removed, and the downtoner claim is marked model-specific.
4. `AP-027`'s human rewrite named a "Sarah". Russell et al. found an Emily or a Sarah in 63 to 70 percent of GPT-4o and Claude 3.5 articles, so the example now uses another name and says why.

## Rejected, with the numbers

- **`participial_clause_density`** (the largest effect in Reinhart et al.: present participial clauses at 5.3 times the human rate in GPT-4o, d=1.38). A sentence-initial or sentence-final participle approximation flags 4.1 percent of AIGEN sentences, against 5.6 percent of WIKI2021, 2.5 percent of T2, 1.0 percent of ESSAYS and 4.6 percent of T1. Windows of 4 or more in 8 sentences: 0 in AIGEN, 8.8 per 10k in WIKI2021. The effect does not show on current Claude output, and encyclopedic prose is the heavier user. A tagger might measure it better, but nothing here suggests the signal would separate the registers this server sees. **Do not re-attempt without a fresh model sample that shows the gap.**
- **`nominal_binomial_density`** ("transparency and accountability"; Reinhart et al. 1.9 times for phrasal coordination, 2.1 for nominalizations). 0 in AIGEN against 37.2 / 12.4 / 29.6 per 10k on T2 / ESSAYS / WIKI2021. Inverted.
- **`hedged_contrast`** ("is not simply", "rather than merely"; Graphite up to 576 times). 22.6 per 10k on ESSAYS, almost all "is not merely", an ordinary essayist's construction. Fails the bar by a factor of four.
- **"more than you think / realize"** without "matters": 9 on ESSAYS (2.6 per 10k), all legitimate.
- **"the real lesson here"**: 2 on ESSAYS, both Paul Graham's own idiom. `credibility_insistence` already counts "real" density.
- **Bold-label bullet runs and emoji headings** as a detector: none of the corpora contain markdown, so any zero would be blind, and READMEs use bold labels legitimately. Carried as a `self_review` item instead.
- **Reporting-verb substitution** ("notes" and "explains" for "says"): document-scoped and register-dependent; a `self_review` item.
- **Reader-contact absence** (no I, you or question in an essay): content-type-dependent and high-FP outside essay registers; a `self_review` item.
- **Scene-setting news openers** ("On a drab November morning"): delayed ledes are normal in feature journalism.
- **Lexical diversity, homogenization, slop-dimension scores**: the first is model-dependent (above), the second is a population property no single text exposes, the third has annotator agreement of kappa 0.29 or lower.
- **"Contrary to popular belief", "Something shifted", "What remains is"**: each appeared once in the default sample and nowhere in human prose, but a single observation with no published support is a fitted rule. Recorded here so a later round with a larger sample can pick them up.
