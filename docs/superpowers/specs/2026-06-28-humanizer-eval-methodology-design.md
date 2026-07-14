# Humanizer Evaluation Methodology: Validating the MCP

**Date:** 2026-06-28
**Status:** Approved for planning
**Author:** Nico Jan (architecture by Claude)

## Decision (locked)

The humanizer ships as **100% an MCP server**, not a Claude skill, not a
hybrid. Reasoning, both independent and both decisive:

- **Consumer reach.** The intended consumer is "any LLM / automated pipelines."
  A Claude skill is Claude-only by nature and cannot serve non-Claude models at
  all.
- **Update propagation.** A hosted MCP updates centrally: push once, every
  consumer gets the new rules on its next call, zero client action. A
  distributed skill drifts stale: a manually-copied folder never updates, a
  git-repo skill needs `git pull`, and a marketplace plugin auto-updates only if
  the user opted into a marketplace with auto-update on (default ON only for
  official Anthropic marketplaces; off for self-hosted).

The skill's one real edge (rules sitting in-context while the model writes) is
a difference of *degree*, not a capability gap: an MCP client instructed to run
`check_text` and fix what it flags gets the same write→check→fix loop. **All
rules are kept.** The MCP was never the problem; whether the rules get *followed*
is the open question this methodology answers.

**Second decision (locked): the evaluation makes no API calls and uses no models,
anywhere, including dev tooling.** The instrument is therefore deterministic
statistics only: L0 (checker compliance) + texture features (§4). The
LLM-as-judge (the old L1) is removed, and the Step-1 harness does not generate
text: it scores outputs you produce and provide. This trades discrimination
ceiling for zero dependencies and full offline reproducibility; the Step-0 spike
tests whether the deterministic signal is strong enough to trust. If it is not,
the fallbacks are a heavier *local* model (e.g. Binoculars, still no API), human
rating, or keeping the MCP as-is, not an API judge.

## 1. The surviving question

With the architecture decided, one question remains unverified, and there is no
instrument to answer it:

> **Adherence.** Do LLMs actually *produce output that follows* the rules, and
> what, within the MCP's reach, maximizes that?

"It got large" and "we have no evidence it works" are the same fact: with no way
to measure adherence, we can't tell whether the rules get applied, whether
reading them helps, or whether the check→fix loop is doing the real work. This
methodology builds that instrument and uses it.

## 2. Goal

A **method to prove the MCP demonstrably works and to find what maximizes
adherence**:

- Establish whether having + reading the rules changes output at all.
- Establish how much of "following the rules" comes from *reading* them versus
  from an enforcement **write → check → fix loop**.
- Confirm both hold across more than one writer model (the consumer is "any
  LLM").

Findings feed back into how the MCP is *meant to be used* (e.g. whether the
application protocol should mandate the loop), not into pruning rules.

## 3. Core principle: instrument before everything

Treat this as a measurement problem. The missing piece is an instrument that
scores a produced text on two things: **how well it follows the rules**
(adherence) and **how human it reads** (quality). Everything downstream depends
on it.

The load-bearing question:

> Can we measure adherence and human-likeness **cheaply** enough to run in a
> loop, and **validly** enough that the numbers track reality?

If yes, the surviving question is answerable. If no, we keep the MCP as-is and
stop guessing. **So the method's first action de-risks this before anything else
is built** (§7, Step 0).

## 4. The instrument (layered measurement signal)

Two distinct measurements, because the experiment needs both (see §6.3):

**Adherence**: does the output obey *our* rules?
- **L0: Checker.** The existing `check_text` findings, normalized per 1k words
  and **weighted by severity** (`hard_violation` > `must_clear` >
  `manual_review`), not a flat count. This *is* the adherence metric. Objective,
  free, deterministic. **Important: L0 measures compliance with our house style,
  not "humanness."** The rules deliberately ban things humans do (em-dashes,
  above all), so genuine human text trips L0 too. L0 and human-likeness (texture)
  can therefore diverge, and that divergence is itself informative (it tells us
  whether a rule is well-calibrated; see §6.3, §8). L0 is **not** a human/AI
  discriminator.

**Human-likeness**: does it read like a person wrote it? Measured by
**deterministic texture features** (`eval/scorers/texture.py`), no models, no
API:

| Feature | Signal |
|---|---|
| `sentence_length_stdev` (burstiness) | Humans vary sentence length; LLMs run even. The lead discriminator. |
| `sentence_length_range` / `_mean` | Distribution shape of sentence lengths. |
| `type_token_ratio`, `hapax_ratio` | Lexical diversity. |
| `mean_word_length`, `bigram_repetition` | Word/phrase repetition texture. |

None is trusted in isolation. The Step-0 spike computes per-feature separation
(direction-agnostic `max(auc, 1-auc)`) over the human/AI piles and reports which,
if any, clears the bar. A periodic **human anchor** (blind A/B by a person)
remains the ground-truth validity check, run rarely, never via API.

The human-likeness target is **generically human writing**: a diverse,
multi-author corpus, not any one person's voice. This is a public tool open to
everyone, so the bar is "reads like a person wrote it," not "reads like a
specific person."

### 4.1 The detector-evasion trap (due-diligence finding)

Even with a deterministic signal, the north star is **"reads human to a human,"
not "beats a detector."** Tuning the rules to maximize a separation statistic (or
to evade a specific AI-detector) turns this into StealthGPT-style bypass tooling:
an arms race, ethically grey, off-goal. The texture features are diagnostics
validated against the human anchor, never an evasion target. On humanized text,
off-the-shelf detectors disagree wildly (GPTZero ~93%, Pangram ~50%, Originality
~57%), exactly why we don't chase any single one.

## 5. The benchmark (the fixed thing we measure against)

A versioned, in-repo set of **writing tasks**, not rules.

- **Tasks**: ~20-30 to start, spanning the genres the system claims to serve.
  Reuse the taxonomy in `content_profiles.json` so the eval maps onto what is
  deployed. Each task = prompt + genre tag + (optional) human gold exemplar.
  Small enough to run often, big enough to learn from.
- **Calibration sets**: known-human text (a diverse, multi-author sample, per
  genre) and known-AI text (raw model output), for the Step 0 spike and L2/L3
  calibration. These genre-matched human samples double as the L1 judge's
  reference exemplars, so per-task gold exemplars are genuinely optional.
- **Growth rule (TDD for tells)**: when a new in-the-wild tell appears (like the
  PR2 portfolio audit), it enters as a **benchmark case first** (a text
  exhibiting it) so any checker/rule change can be verified to catch it without
  regressing other cases. The benchmark is the regression suite.

## 6. The experiment

> **Reconciled with the second locked decision (no API).** Throughout §6-§8,
> read "human-likeness (L1/L2)" as the §4 **deterministic texture features**, not
> an LLM judge. The harness does **not** generate text: you produce outputs under
> each condition and the harness scores the provided files (so "writer model" =
> whatever produced those outputs, recorded as metadata). Step 1 implements only
> `unaided` vs `rules`; the `rules+loop` condition and its anti-circularity split
> are Step 2.

### 6.1 Design: condition × writer-model

The architecture is fixed (MCP), so the variable is **how the MCP is used**:

- `unaided`: control; the model writes the task cold, no rules, no checker.
- `rules`: the model has the rules available via the MCP and reads them, single
  pass. (Does having + reading the rules change output at all?)
- `rules+loop`: the model writes, calls `check_text`, fixes flagged items, and
  repeats. (Does the enforcement loop add adherence/quality on top of reading?)

**How conditions are realized in the harness.** To measure cleanly, the harness
*controls context directly* rather than depending on each model's live
tool-calling discipline: `rules` = task prompt + the MCP's served rule payload
injected into context; `rules+loop` adds iterative `check_text` calls + revision.
This measures the **ceiling**: what happens when the rules are actually present,
not whether a given client bothers to retrieve them. Retrieval discipline (does
a model proactively call the tools mid-write) is real but client-specific and out
of scope for this first experiment.

**Writer models:** at least two: a frontier model and a weaker/open one. The
consumer is "any LLM," and an approach that only works for frontier models is a
different product than one that works for weak ones. Per-writer results are a
finding, not noise. (Roster chosen at implementation; see §9.) Note: if the
frontier writer is also the strongest model available, the L1 judge can be a
*different* model of similar strength rather than a stronger one; the rubric and
the L3 anchor carry the validity.

Tasks = the benchmark. Each cell → both measurements (adherence + human-likeness).

### 6.2 What each question reads off the grid

- **Does reading the rules help?** `unaided` vs `rules`, on adherence (L0) *and*
  human-likeness (L1).
- **Does the loop carry the weight?** `rules` vs `rules+loop`: judged on
  human-likeness per §6.3. If the loop is where the benefit lives, the MCP's
  application protocol should mandate it, not treat it as optional. Caveat: the
  loop only enforces the **mechanizable subset** the checker covers (em-dash,
  punctuation, banned structures, density, uniformity); the rest of the corpus
  (most lexical/discourse/psycholinguistic guidance) is read-time only. So
  `rules+loop` = read-time application of all rules + loop enforcement of the
  checkable subset. This is also why the corpus still matters even if the loop
  carries adherence.

### 6.3 The anti-circularity rule (critical)

If "adherence" (L0) is the score, a loop that fixes whatever L0 flags **wins L0
by construction**: a rigged comparison. So the dependent variable differs by
question:

- **`unaided` vs `rules` (no loop):** L0 adherence is valid: neither condition
  optimizes against the checker.
- **Loop value (`rules` vs `rules+loop`):** judge on **human-likeness (L1/L3)**,
  never L0. The only honest question about the loop is "does it make text *more
  human*, or merely better at dodging my regexes?" Watch for over-correction: a
  loop can satisfy every rule and still produce stilted prose; L1/L3 catches
  that, L0 cannot.

## 7. Buildable sequence (not boil-the-ocean)

- **Step 0: Signal spike (half a day).** ~15 known-human + ~15 known-AI texts
  through the scorers. The separation test is on **L1/L2** (the human-likeness
  signal): *do their scores separate the piles?* L0 is **not** run as a human/AI
  discriminator (it measures house-style compliance; human text trips it too),
  so Step 0 only sanity-checks that L0 runs and that AI text trips more *structural*
  tells than human text on average. **Define the go/no-go bar up front** (e.g. a
  clear margin between the human and AI L1-score distributions, or an AUC
  threshold) so it is not a judgment call. If no cheap human-likeness signal
  separates human from AI on obvious cases, it cannot grade subtle output and the
  plan is dead: keep the MCP as-is. **Riskiest assumption, tested first.**
- **Step 1: Minimal harness.** Run a slice of the §6 grid (`unaided` / `rules`,
  one writer, signal = L0 + L1) on a tiny benchmark. Prove the harness produces a
  readable comparison.
- **Step 2: Full experiment.** Benchmark to ~20-30 tasks, add L2 and the
  `rules+loop` condition, run across ≥2 writers. Produce the decision grid for
  §6.2.
- **Step 3: Apply findings to the MCP.** e.g. if the loop carries adherence,
  make `check_text` + a documented write→check→fix protocol the centerpiece of
  how the MCP is meant to be used; tighten the application protocol accordingly.
  All rules retained.
- **Step 4: Standing regression harness.** Benchmark + instrument become the
  gate: any rule or serving change must hold or improve adherence/human-likeness
  on the suite before shipping.

Each step is gated by the previous one.

## 8. Likely (non-binding) product implication

Prior, to be confirmed or refuted by Step 2: **the enforcement loop, not the act
of reading rules, is what produces adherence.** One-shot rule-reading has a low
ceiling; write → check → fix is what makes the rules real. If borne out, the MCP
should present `check_text` and the loop as the primary intended usage, with the
reference readers as support, all rules kept. A hypothesis the method tests, not
a decision.

## 9. Risks and open questions

- **Instrument invalid (highest risk).** Mitigated by Step 0 first and cheapest.
- **Circularity / Goodhart.** L0-as-loop-target is rigged; handled by §6.3.
  Optimizing L2 is the evasion trap; handled by §4.1.
- **Judge bias** (verbosity, position). Mitigated by rubric + reference + bias
  controls in L1.
- **Benchmark too small for significance.** Early goal is *direction*, not
  significance; grow only once the instrument is trusted.
- **Human corpus sourcing (resolved).** Use a diverse, multi-author public
  human-written sample per genre for L1 references and L3 anchors: the target is
  generically human, not one person's voice. Specific sources chosen at
  implementation.
- **Open: writer-model roster.** Which frontier + which weak/open model, and how
  a pipeline drives a non-Claude model through the loop condition.
- **Open: harness location.** Lean `eval/` in this repo so cases, rules, and
  checker version together.

## 10. Success criteria

- **Step 0:** a documented yes/no (with numbers against a pre-set bar) on
  whether the human-likeness signal (L1/L2) separates human from AI text.
- **Step 2:** a decision grid that says whether reading the rules helps and
  whether the check→fix loop is where adherence comes from, on evidence.
- **Standing:** a regression harness such that no rule or serving change ships
  without holding adherence and human-likeness on the benchmark.
