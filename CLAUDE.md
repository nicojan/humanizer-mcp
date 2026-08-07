# mcp-humanizer

An MCP server that provides psycholinguistic, lexical, structural, and discourse-level rules for producing naturally human-sounding written content. It serves as a reference for Claude during writing and revision tasks: the server supplies rules and examples, and Claude applies them.

Server name: `humanizer_mcp` (Python convention: `{service}_mcp`)
All tool names prefixed with `humanizer_` to avoid conflicts with other MCP servers.

## Reference Docs

| File | Load When |
|---|---|
| `docs/PRD.md` | Understanding what this server does and its role in the ecosystem |
| `docs/DATA_SCHEMA.md` | Modifying data file structure or adding new data files |
| `docs/API_SPEC.md` | Adding or modifying tools: parameter specs, validation, error handling |
| `docs/DEPLOYMENT.md` | Deploying, redeploying, or debugging infrastructure |

## Tech Stack

| Parameter | Value |
|---|---|
| Language | Python |
| Framework | FastMCP (`mcp` package) |
| Storage | JSON files in Git-tracked `/data` directory |
| Transport | Streamable HTTP |
| Auth | None (public, read-only) |
| Container | Docker + docker-compose.yml |
| Host | Any container host; single stateless container behind a reverse proxy or tunnel |
| Port | 8016 (configurable via `PORT`) |
| PUID/PGID | `1026` / `100` |
| TZ | `America/Vancouver` |

See `docs/DEPLOYMENT.md` for deployment and configuration.

## Project Structure

```
mcp-humanizer/
├── CLAUDE.md
├── docs/
│   ├── PRD.md
│   ├── DATA_SCHEMA.md
│   ├── API_SPEC.md
│   └── DEPLOYMENT.md
├── src/
│   ├── __init__.py
│   ├── server.py
│   ├── middleware.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── read.py
│   │   └── check.py
│   ├── checker/
│   │   ├── __init__.py
│   │   ├── emdash.py
│   │   ├── punctuation.py
│   │   ├── phrases.py
│   │   ├── insistence.py
│   │   ├── structures.py
│   │   ├── segment.py
│   │   ├── metrics.py
│   │   ├── loader.py
│   │   ├── inflect.py
│   │   ├── report.py
│   │   └── util.py
│   └── storage/
│       ├── __init__.py
│       └── json_store.py
├── data/
│   ├── foundation.json
│   ├── lexical_patterns.json
│   ├── structural_patterns.json
│   ├── sentiment_tone.json
│   ├── discourse_cohesion.json
│   ├── psycholinguistic_texture.json
│   ├── content_profiles.json
│   ├── anti_patterns.json
│   ├── banned_structures.json
│   ├── caveats.json
│   └── self_review.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements.lock
├── .gitignore
└── README.md
```

## Operational Model

- 13 read-only tools, all prefixed with `humanizer_`: 12 reference readers (`get_summary`, `get_guide`, `get_application_protocol`, `get_foundation`, the six layer getters, `get_content_profile`, `get_anti_patterns`, `get_caveats`) plus the `humanizer_check_text` deterministic compliance checker (read-only w.r.t. server state: it analyzes input and mutates nothing)
- **No runtime write tools** (public-MCP spec rule). Updates flow via `git push` to this repo + container restart; `entrypoint.sh` pulls the latest `data/` on every start
- Per-request access logging via `CFConnectingIPLogMiddleware` (one JSON line per request to stdout)

## Key Constraints

- **Never** use `mcp.run()`; use `uvicorn.run(app, host=HOST, port=PORT)`
- **Never** use `BaseHTTPMiddleware`: it buffers responses and corrupts the Streamable HTTP transport. The CF-Connecting-IP logger is a pure ASGI middleware
- **No runtime write tools** in the deployed binary: this is a public-MCP spec rule
- **Always** set `PYTHONPATH=/app` in the Dockerfile
- **Never** hardcode secrets in `docker-compose.yml`
- **Never** pass unsupported kwargs to `FastMCP()`
- **Always** use Pydantic `BaseModel` with `Field()` for tool input validation
- **Always** strip `meta` blocks from JSON responses to save tokens (preserving `meta.usage` and `meta.application_rule` as top-level fields). `_strip_meta` also recursively drops field-level `research_basis` and `theory` keys (citation/rationale trails for data-file editors that add no value to the LLM during a rewrite). NOTE: `notes` is deliberately not dropped: in `content_profiles.json` the per-layer `notes` are the actionable payload
- **`humanizer_get_foundation` excludes `application_protocol`.** The ~1,950-token phase plan ships only via its own tool (`humanizer_get_application_protocol`) and inside the full `humanizer_get_guide`. Keeping it out of the foundation payload is what makes that tool the genuine "minimum viable" call (~2.3k vs ~4.3k tokens). `build_foundation_payload()` in `src/tools/read.py` is the source of truth
- **Always** use compact JSON (`separators=(",",":")`) in tool responses
- **Always** prefix tool names with `humanizer_`
- **AR-003 (punctuation correctness) is enforced mechanically.** `src/checker/punctuation.py` detects stacked internal marks (hard_violation) and missing terminal marks / run-on spans / comma splices (must_clear). The comma-splice detector (`find_comma_splices`) targets the most common AR-002 side effect (an em-dash pivot between two independent clauses replaced by a bare comma) and stays conservative: it fires only on `comma + subject-pronoun + finite verb` and skips complex sentences (leading subordinator), parentheticals, compound sentences (`, but …`), lists, and non-finite intros (`To …`, `Having …`, `Frustrated …`). Any new checker module should keep the same false-positive discipline: legitimate `etc.,` and `...` must not trip a hard rule
- **Research-backed discourse/structural tells (added 2026-06, all `must_clear`, never `hard`).** The checker also surfaces, as clearable findings: the discourse antithesis structures `BS-013` `negation_flip_antithesis` (the "it's not X, it's Y" two-sentence copula flip: the single most characteristic LLM rhetorical tell), `BS-014` `rarely_flip_aphorism`, `BS-015` `wh_cleft_pronouncement`, `BS-016` `meta_framing_opener` (all `regex`/`checklist` in `banned_structures.json`, auto-wired via the loader); plus two statistical detectors: `rule_of_three_density` (`src/checker/structures.py`, clustered three-item lists) and `segment_uniformity` (`src/checker/metrics.py`, flat style across ≥3 sections, the durable cross-segment signal). New lexical flags `underscore`/`surpass`/`boast` were added to `flagged_verbs`. Rationale and citations live in `data/caveats.json` (`flow_over_surface_features`, `sentence_length_mean_not_a_signal`, `em_dash_model_specific`): surface word swaps are necessary hygiene with a low ceiling; flow and section-to-section variation are the durable signals. The em-dash ban (AR-002) is unchanged; `em_dash_model_specific` only documents that em-dash *rate* is a model-specific statistic, not grounds to relax the ban
- **PR2 in-the-wild tells (added 2026-06-28, `docs/proposed-rules-2026-06-28.md`, all `must_clear`/`manual_review`, never `hard`).** Empirical findings from a portfolio audit that passed the June checker clean. (1) `credibility_insistence`, a *density* detector (`src/checker/insistence.py`) for reality-assertion overuse (`real`/`actual`/`genuine`/`truly`…); config (token set + thresholds + exclusions for `real-time`/`real estate`/quoted/interrogative) lives in `lexical_patterns.credibility_insistence`, loaded via `loader.load_credibility_insistence`. (2) Four new `banned_structures`: `BS-017` `disclaimer_reversal` and `BS-019` `locative_pseudocleft` (regex, auto-wired); `BS-018` `copula_maxim_closer` and `BS-020` `verb_antithesis_pair` (`method=heuristic`, implemented in `src/checker/structures.py` like `BS-009`/`BS-012`). (3) Abstraction-as-agent is a `manual_review` line only (+ `AP-033`). Two detectors were deliberately tightened beyond the proposal to keep the FP discipline: `BS-019` requires an article-led NP subject (skips `This is how`/`Here is where`), and `BS-020` verifies the negated verb is actually repeated from the prior sentence (skips `It never finished.`)
- **`BS-021` `noun_participle_fragment` (added 2026-07-03, in-the-wild reviewer feedback, `must_clear`, never `hard`).** The verbless "Noun, past-participle." sentence: a determiner-led NP, a comma, and a trailing past participle, ending there (`The same board, rebuilt.`, `The homepage, reimagined.`). Past-participle sibling of `BS-005` (present-participle tail). Implemented as a **regex** in `banned_structures.json` (auto-wired via `loader.load_regex_structures` → `find_regex_structures`; **no code change**, so it deploys data-only), with `AP-034` as its `source_examples` anti-pattern. Three FP guards keep it near-zero: the subject must be a **sentence-initial** determiner-led NP (skips `He left the room, defeated.`), the participle must be the **terminal token** so the sentence is bounded to a verbless fragment (skips `The board, which we rebuilt, is live.` and `The report, revised, was sent.`), and a `[a-z]{3,}ed` length floor plus an explicit irregular list excludes short `-ed` look-alikes (`red`/`bed`/`shed`). Idioms without the comma (`Case closed.`) never match; the comma is definitional. Spec: `docs/superpowers/specs/2026-07-03-noun-participle-fragment-rule-design.md`; tests: `tests/checker/test_noun_participle_fragment.py`
- **`BS-022` `meta_label` + the "performative framing beat" self-review item (added 2026-07-06, in-the-wild feedback on humanized content, all `must_clear`/`manual_review`, never `hard`).** The "performative framing beat" is a self-aware flourish that performs insight/closure rather than carrying content, in three sub-forms: a self-satisfied closer, a meta label, and a paradox headline. Split by mechanizability. (1) The **meta-label** slice, a standalone line/heading naming the artifact's own format or length instead of its subject (`In 200 words`, `In brief`, `The short version`, `At a high level`, `To put it simply`), is `BS-022`, a **regex** in `banned_structures.json` (auto-wired via `loader.load_regex_structures`; **no code change**, deploys data-only), `AP-035` as its `source_examples`. `TL;DR` is deliberately excluded. The FP guard is **terminal-only**: the label must be the whole bounded line (optional single terminal mark, then line-end/string-end), so embedded uses (`At a high level, the system does X.`) never match; this is what makes it safe to include the embedding-prone phrases. It does **not** add a closer regex (that FP risk is why the closer stays judgment-only); `BS-018` `copula_maxim_closer` remains the mechanical closer detector. (2) The **judgment** sub-forms (self-satisfied closer, first-person meta-commentary on the work, paradox-substitution headline) are a new `data/self_review.json` `manual_review` item, with the definitional caveat baked in: one aphorism/paradox is legitimate: the tell is *repetition and substitution for content*, not the device. Rationale: `caveats.json` `performative_framing`. Spec: `docs/superpowers/specs/2026-07-06-performative-framing-beat-design.md`; tests: `tests/checker/test_meta_label.py`, `tests/checker/test_self_review.py`
- **`BS-023`/`BS-024`/`BS-025` + lexical/self-review additions (added 2026-07-13, from a web survey of current AI-writing tells cross-checked against existing coverage, all `must_clear`/`manual_review`, never `hard`).** Three new **regex** `banned_structures` (auto-wired via `loader.load_regex_structures`; **no code change**, deploys data-only): `BS-023` `validation_reassurance` (`AP-036`), the fixed second-person reassurance frame (`You're not alone.`, `You're not imagining it.`, `It's not just you.`), the single most-cited *new* 2026 tell; frame-scoped to the `you're not <predicate>`/`it's not just you` forms so ordinary negations (`You're not sure yet.`) never match, and the pattern accepts both straight and curly apostrophes. `BS-024` `vague_authority_attribution` (`AP-037`), appeals to an unnamed authority (`Studies show…`, `Experts agree…`, `It is widely believed…`); scoped to unnamed-agent + epistemic-verb frames so a named/specific reference (`The researchers at MIT published…`) passes; distinct mechanism from `credibility_insistence` (reality-assertion density). `BS-025` `question_fragment_cadence` (`AP-038`), the `The best part? It's this.` determiner-led NP-fragment question answered in the next breath; the determiner must sit at a sentence boundary and the NP is ≤3 words, so WH-questions (`What is the best part?`) and mid-sentence questions (`Did you see the result?`) never match. Plus lexical list extensions in `lexical_patterns.json` (openers `Additionally`/`Consequently`/`Notably`/`Importantly` in `flagged_transitions`; `bustling`/`breathtaking` adjectives; `hidden gem` noun) and one `self_review.json` item (excessive coherence / tidiness). **Two candidate tells were deliberately rejected on evidence, not style:** (1) curly/smart-quote detection, a tooling artifact rather than an author signal; the eval corpus's own `SOURCES.md` normalization note records raw *human* web text as curly and raw *AI* output as straight (inverted for this domain), and modern model UIs emit curly quotes anyway, so it discriminates nothing reliable; (2) a bare `quiet` word-flag, an ordinary word whose "tell" is register/collocation, the exact `flow_over_surface_features` low-ceiling trap. Verified: 269 tests green; **0/16 structural false positives** on the genuine-human eval corpus; ReDoS-safe (sub-300ms on 200k pathological chars). Tests: `tests/checker/test_validation_reassurance.py`, `test_vague_attribution.py`, `test_question_fragment.py`, `test_promotional_lexicon.py`
- **`BS-026`..`BS-030` + marketing-lexicon additions (added 2026-07-25, `docs/proposed-rules-2026-07-25.md`, from a survey of current phrase-frame tells against existing coverage, all `must_clear`, never `hard`).** Five new **regex** `banned_structures` (auto-wired via `loader.load_regex_structures`; **no code change**, deploys data-only), closing the checker's biggest verified gap, fixed phrase-frame openers and marketing pivots, which the 23 prior structures (strong on *rhetorical* tells) missed. `BS-026` `when_it_comes_to_opener` (`AP-039`): the "When it comes to X, ..." empty topic preamble; sentence-boundary + trailing-comma scoped so mid-sentence "she knew when it comes to a vote" never matches. `BS-027` `world_state_opener` (`AP-040`): "In a world where… / In an era of… / In an age where…" sweeping openers; boundary + fixed determiner-noun-`where/of` skeleton so literal "in a world of magic" passes. `BS-028` `pivotal_role_frame` (`AP-041`): the "plays a [pivotal/crucial/key/central] role in" filler template; restricted to an evaluative-adjective allow-list so neutral "play a supporting role in the film" passes (the template slips prior lexical flags when the adjective is un-flagged, e.g. key/central/major). `BS-029` `solution_pivot` (`AP-042`): the "That's where X comes in." marketing pivot; sentence-initial + **terminal-scoped** (`comes in[.!?]`) so the idiom "comes in handy" and locatives ("this is where we live") never match. `BS-030` `empathy_conditional_opener` (`AP-043`): the "If you've ever struggled with…" manufactured-empathy hook (family of `BS-023`); boundary + an **empathy-verb allow-list** (struggled/wondered/felt/…) so anecdotal "If you've ever been to Paris" and mid-sentence uses pass; accepts straight and curly apostrophes. Plus a curated marketing/promotional lexicon in `lexical_patterns.json`: verbs (`unlock`, `unleash`, `embark`, `empower`, `elevate`), adjectives (`vibrant`, `invaluable`, `unwavering`, `ever-evolving`), nouns (`treasure trove`, `plethora`, `myriad`). **Candidates rejected on evidence, not style:** register-dependent openers (`Here's the thing`, `Let's be honest`) as the `flow_over_surface_features` trap, and legitimate high-frequency human discourse markers (`in other words`, `that said`, `to be clear`). Verified: full checker suite green (248 tests; the `tests/tools/*` suite is blocked by a pre-existing pydantic-core env mismatch, unrelated to this change); **0/16 structural false positives** on the genuine-human eval corpus; ReDoS-safe (~34ms on 200k pathological chars). NOTE: the eval corpus predates these 2026 frames, so it validates FP-safety, not recall, recall is covered by the constructed unit tests. Tests: `tests/checker/test_phrase_frames_2026_07.py`, `test_lexicon_2026_07.py`
- **`metrics_do_not_apply_to_label_text` (added 2026-08-03, `data/caveats.json`, caveat only, no code).** The prose metrics are undefined on headline/label/fragment input and the structural coverage is prose-shaped, so short label copy both fails spuriously and passes undeservedly. Measured on the chrome of a slide deck (11 act names, titles and section descriptors as one document): `prohibitions_clear` true with one `must_clear`, `burstiness` at stdev 1.0 against target 6.0 on a 3.5-word mean, while two genuine label-register tells in the same input (`Eight words to carry`, `Your answer first`) went unflagged, because the `banned_structures` are frames drawn from prose and an empty evaluative subtitle is not one of them. Guidance (**corrected 2026-08-03, same day**): the rule is about which findings to read, not whether to run the check. Run it on label copy and on deliberately simple body text alike, and read `hard_violations`, the `banned_structures` and the lexical flags, all of which stay meaningful at any length; ignore `burstiness` and `segment_uniformity`. The first wording said not to run it on CEFR-pitched text at all, which was wrong: a real 139-word B1 slide set came back `prohibitions_clear` with zero hard violations, and skipping the run would have left AR-002 and the phrase-frame structures unchecked on student-facing copy. **Deliberately documented rather than detected**: a heuristic guessing "this input is labels" from length or punctuation would misfire on real short-form prose, which is the `flow_over_surface_features` cry-wolf trap. Consumer: `human-lesson-builder` now tells deck authors to check deck chrome and only deck chrome.
- **`BS-031`..`BS-037` + abstract-prestige lexicon + the AR-002 markdown fix (added 2026-08-06, `docs/proposed-rules-2026-08-06.md`, from an in-the-wild report that metaphorical `carry` is unflagged plus a survey of tells published since the July round; all `must_clear`, never `hard`).** Seven new **regex** `banned_structures` (auto-wired via `loader.load_regex_structures`; **no code change** for the rules themselves, so they deploy data-only). `BS-031` `metaphorical_carry` (`AP-044`): the batch's trigger: the `carries/carried/carrying the weight|burden|meaning` collocation plus the text-unit intransitive (`eight words to carry`), the exact tell `caveats.json` `metrics_do_not_apply_to_label_text` recorded going unflagged on 2026-08-03. **Deliberately not a bare `carry` word-flag** (the `flow_over_surface_features` trap that killed bare `quiet`), and `load`/`freight` were dropped from the object list mid-build after a boundary probe fired on `the truck carries the load to the depot`. The open-ended abstract-subject-of-`carry` family stays a `self_review` judgment call: that rubric item (abstraction-as-agent) was extended to name `carry` as its most frequent and hardest-to-hear instance. `BS-032` `honestly_fragment_opener` (`AP-045`): the standalone `Honestly?` candour fragment; whole-bounded-fragment anchoring means quoted dialogue passes. `BS-033` `quiet_prestige_modifier` (`AP-046`): `quiet confidence` / `quietly reshaping`; this **revisits and upholds** the 2026-07-13 rejection of a bare `quiet` flag by scoping to the collocation, allow-listed on both branches so `a quiet room` passes. `BS-034` `concessive_balance_hedge` (`AP-047`): `While X has benefits, it also carries risks`, the both-sides frame that concludes nothing; hedge verb and object both allow-listed. `BS-035` `internal_cross_reference` (`AP-048`): `As mentioned above` and relatives; legitimate in long reference docs, hence checklist. `BS-036` `deepening_invitation` (`AP-049`): `Let that sink in.`, a fixed phrase set. `BS-037` `withheld_insight_teaser` (`AP-050`): `Here's the kicker` / `the part most people miss`; scoped to the withheld-insight *claim*, so the bare `Here's the thing` marker stays unflagged and the 2026-07-25 rejection stands. Plus the abstract-prestige metaphor lexicon in `lexical_patterns.json` (`mosaic`, `symphony`, `labyrinth`, `beacon`, `bedrock`, `cacophony`, `kaleidoscope`, `odyssey`, `crucible`, `north star`, plus `resonate` and `compelling`, all from the arXiv:2412.11385 focal-word cluster the existing `realm`/`tapestry`/`landscape` entries only half-covered). **One real code change shipped with this batch, found by dogfooding:** `src/checker/emdash.py` flagged markdown table separators (`|---|---|`), horizontal rules, setext underlines and front-matter fences as the `--` em-dash digraph. Since AR-002 is a **hard** gate, that false positive made `prohibitions_clear` unreachable for any document containing a table. `find_emdashes` now skips hyphen runs on a line composed only of `-`, `|`, `:` and spaces; a genuine inline `word--word` is still flagged. **This one needs a rebuild, not just a restart.** Verified: 414 tests green; **0/16 structural false positives** on the genuine-human eval corpus; ReDoS-safe (133ms on 330k pathological chars); the design doc itself checks `prohibitions_clear` true. As with the July round the eval corpus predates these frames, so it validates FP-safety, not recall. Tests: `tests/checker/test_tells_2026_08.py`, plus the markdown cases in `tests/checker/test_emdash.py`
- **Self-review rubric (added 2026-06-29, `data/self_review.json`).** The human-likeness half of write→check→fix: the deterministic checker catches the mechanizable tells; the rubric is the texture checks it cannot verify (rhythm, reused rhetorical shape, section-to-section variation, generic competence/stance, abstraction-as-agent), which the **calling model** runs against its own draft. It is surfaced as the `humanizer_check_text` report's `manual_review` list (previously a hardcoded list in `report.py`, now data-driven via `loader.load_self_review`) and sequenced by `next_action`. The server makes **no API call**: it returns the rubric, and the calling model does the judging in its own turn. Edit the data file and git-push to update. `assemble_report` keeps a static fallback list so direct callers still work. The `test_pr2_additions` abstraction-as-agent assertion pins that item's presence in the data file
- DNS rebinding protection is **enabled** in `src/server.py`. The allowlist is built from the `PUBLIC_HOST` environment variable plus the localhost entries for the configured `PORT`. Set `PUBLIC_HOST` to the hostname you serve under; if it does not match the incoming `Host` header, every legitimate request returns 421
- **`foundation.primary_usage` (v1.3.0, added 2026-06-29) is evidence-backed.** The write→check→fix loop is documented as the *primary, required* path to adherence (not optional polish), justified by the deterministic eval: reading the rules roughly halved house-style violations but the verification loop is what cleared the rest to zero, with no loss of human-likeness. The supporting experiment is `eval/FINDINGS.md` (Step 2 decision grid). The `eval/` directory is **dev-only tooling** (no API, no models) that never ships in the Docker image or `data/`; only `data/foundation.json`'s `primary_usage` field is the deployed artifact of this work. Methodology: `docs/superpowers/specs/2026-06-28-humanizer-eval-methodology-design.md`; corpus: `eval/corpus/SOURCES.md`
