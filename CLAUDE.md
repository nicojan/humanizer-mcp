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
- **Self-review rubric (added 2026-06-29, `data/self_review.json`).** The human-likeness half of write→check→fix: the deterministic checker catches the mechanizable tells; the rubric is the texture checks it cannot verify (rhythm, reused rhetorical shape, section-to-section variation, generic competence/stance, abstraction-as-agent), which the **calling model** runs against its own draft. It is surfaced as the `humanizer_check_text` report's `manual_review` list (previously a hardcoded list in `report.py`, now data-driven via `loader.load_self_review`) and sequenced by `next_action`. The server makes **no API call**: it returns the rubric, and the calling model does the judging in its own turn. Edit the data file and git-push to update. `assemble_report` keeps a static fallback list so direct callers still work. The `test_pr2_additions` abstraction-as-agent assertion pins that item's presence in the data file
- DNS rebinding protection is **enabled** in `src/server.py`. The allowlist is built from the `PUBLIC_HOST` environment variable plus the localhost entries for the configured `PORT`. Set `PUBLIC_HOST` to the hostname you serve under; if it does not match the incoming `Host` header, every legitimate request returns 421
- **`foundation.primary_usage` (v1.3.0, added 2026-06-29) is evidence-backed.** The write→check→fix loop is documented as the *primary, required* path to adherence (not optional polish), justified by the deterministic eval: reading the rules roughly halved house-style violations but the verification loop is what cleared the rest to zero, with no loss of human-likeness. The supporting experiment is `eval/FINDINGS.md` (Step 2 decision grid). The `eval/` directory is **dev-only tooling** (no API, no models) that never ships in the Docker image or `data/`; only `data/foundation.json`'s `primary_usage` field is the deployed artifact of this work. Methodology: `docs/superpowers/specs/2026-06-28-humanizer-eval-methodology-design.md`; corpus: `eval/corpus/SOURCES.md`
