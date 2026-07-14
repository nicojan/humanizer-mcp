# Humanizer eval: Steps 1-2 findings (recorded 2026-06-29)

> **CORRECTION (2026-06-29 audit).** The original Q2 conclusion below ("the loop
> improves human-likeness") was an artifact of reading the proxy in the wrong
> direction. In this corpus the AI pile scores **higher** on hapax than human
> (human mean 0.756 vs AI 0.819; `python -m eval.spike` now prints this), so the
> loop *raising* hapax moves text **away from the human mean toward the AI side**,
> not toward human. Re-scored against distance to the human mean and with a
> length-robust diversity proxy (`mattr`, since the loop also shrinks text 13-35%
> and hapax is length-sensitive), **both proxies move AWAY_FROM_HUMAN for both
> writers** (`python -m eval.grid`). The **adherence** result (Q1, and the loop
> driving L0→0) stands unchanged. What changed is the human-likeness claim: it is
> **not supported** by the evidence and the one validated discriminator trends
> mildly the wrong way. With no human anchor we also cannot conclude the loop
> *harms* perceived human-likeness: the honest status is "unproven, proxy
> evidence mildly negative." See the revised Q2 and Conclusion below.

Deterministic, no API. Outputs scored: `eval/outputs/<writer>/<condition>/<task>.txt`
(2 writers × 3 conditions × 4 tasks = 24). Conditions realized per spec §6.1:
`unaided` (cold, no rules), `rules` (full served guide payload in context, single
pass, no checker), `rules_loop` (same + a write→check→fix loop running the deployed
`run_checks`, max 3 iterations). Writers: **primary = Claude Sonnet**, **weak =
Claude Haiku**. Tasks: the four in `eval/tasks.py`.

> **Scope honesty.** n = 4 per cell; both writers are Claude-family (no non-Claude
> / open model). This is **direction only**, not significance, exactly as the
> methodology scopes Step 2's first pass. The decision below rests on the
> direction being large and consistent across both writers and aligned with the
> pre-registered §8 hypothesis, not on statistical power. Multi-vendor writers
> and a larger benchmark remain open (see "Not done").

## Decision grid

Reference bands (Step-0 corpus, n=16 each): hapax human mean **0.756** / AI **0.819**;
mattr human mean **0.819** / AI **0.848**. On both, **human is lower than AI**, so
*lower is more human* and a rise is a move toward the AI side.

| writer | condition | words | L0/1k | hapax (z to human) | mattr (z to human) | sent_sd |
|---|---|---|---|---|---|---|
| primary (Sonnet) | unaided | 151 | 30.112 | 0.785 (+0.48) | 0.844 | 8.495 |
| primary (Sonnet) | rules | 173.2 | 16.051 | 0.774 (+0.30) | 0.838 (+0.43) | 8.973 |
| primary (Sonnet) | rules_loop | 150.5 | 0.000 | 0.806 (+0.83) | 0.852 (+0.76) | 8.737 |
| weak (Haiku) | unaided | 127 | 32.641 | 0.819 | 0.847 | 6.158 |
| weak (Haiku) | rules | 123.8 | 10.772 | 0.802 (+0.76) | 0.852 (+0.76) | 7.034 |
| weak (Haiku) | rules_loop | 80.8 | 0.000 | 0.865 (+1.80) | 0.860 (+0.95) | 7.971 |

(z = distance from the human mean in human-SD units; AI mean sits at hapax z=+1.04,
mattr z=+0.66. Loop values move *further* from 0 = away from human, toward/past AI.)

Loop iterations to clear: primary 1 each; weak 2-3 each (hand-recorded: the loop
was driven by hand, not an autonomous pipeline; no per-iteration artifacts logged).

## Reading the grid (anti-circularity, spec §6.3)

**Q1: does reading the rules help adherence?** (read on L0; fair, neither
condition optimizes against the checker)
Yes. L0 weighted findings/1k fell **30.1 → 16.1 (−47%)** for the primary writer
and **32.6 → 10.8 (−67%)** for the weak writer. Reading the rules roughly halves
house-style violations.

**Q2: does the write→check→fix loop carry the residual adherence?** (read on
human-likeness texture, NEVER on L0; the loop fixes whatever L0 flags, so its L0
win is rigged by construction)
The loop drives adherence to **L0 = 0.0** for both writers, but that is true *by
construction* (it fixes whatever the checker flags) and is not evidence of
anything. The load-bearing question is whether it does so without a humanness cost.
**The original answer here ("texture improves") was wrong**: it read a rising
hapax as more human, but human text scores *lower* on hapax than AI (see the
reference bands above). Re-scored as distance to the human mean:
- primary: hapax z **+0.30 → +0.83**, mattr z **+0.43 → +0.76**: both **away from
  human**, toward and past the AI mean.
- weak: hapax z **+0.76 → +1.80**, mattr z **+0.76 → +0.95**: both **away from
  human**; hapax lands well past the AI mean (and is inflated by a 35% length
  drop, which is exactly why mattr (length-robust) is the better read, and it
  agrees in direction).

So the loop's lexical-diversity texture moves **toward the AI side, not toward
human**, on both a raw and a length-robust measure. Burstiness is excluded: Step-0
AUC 0.516 means it does not discriminate, so its delta is not a humanness signal.
Caveat in both directions: these proxies have **no human-anchor validation**, so
"away from the human mean" is not proof a reader would find the text less human,
but it is certainly not the *improvement* originally claimed.

**What reading alone missed** (cleared only by the loop): a missing terminal mark,
two `BS-011 x_not_y_contrastive` structures, comma splices, a `wh_cleft`
pronouncement, flagged terms, and, for the weak writer, **em-dashes (AR-002) and
a hard violation** ("in today's rapidly evolving"). The weaker the writer, the more
the single pass left behind, and the more the loop did.

## Conclusion → Step 3

Reading the rules is **necessary but insufficient**: it has a real, large effect
but a low ceiling (residual ~11-16 weighted violations/1k). The **write→check→fix
loop is what makes adherence complete (→ 0)**, and the effect is larger for weaker
writers, which matters because the consumer is "any LLM." This adherence result is
the firm one.

On human-likeness, the corrected read does **not** support the original "improves
it" claim: the loop's only validated texture discriminator (hapax, and its
length-robust cousin mattr) moves **away from the human mean toward the AI side**
for both writers. The defensible statement is narrower: *the loop completes
adherence with no measured loss of human-likeness that we can establish, and a
mild proxy signal in the wrong direction that an unvalidated proxy cannot make
conclusive.* It is **not** established that the loop improves, or preserves,
perceived human-likeness; that needs the human anchor (still open).

Therefore the MCP's intended-usage guidance presents the verification loop as the
**primary, required** path to **adherence** (the supported claim), not as a
human-likeness improver. All rules are retained: this changes *how the MCP is
meant to be used*, per spec §2/§8. Applied in `data/foundation.json` (see the
`primary_usage` field and strengthened `enforcement.verification`); the
human-likeness wording there was softened in the same 2026-06-29 correction.

## Not done (explicit: no silent caps)

- **Multi-vendor writers.** Both writers are Claude-family. A non-Claude / open
  model is the spec's intended weak arm and remains open.
- **Benchmark size.** 4 tasks. Growth to ~20-30 is gated on trusting the
  instrument (human anchor), not yet done.
- **Human anchor.** No blind human A/B has validated the texture proxies as
  human-likeness ground truth. `hapax_ratio` discriminates (Step-0 AUC 0.82) but
  in the AI-higher direction; `mattr` is its length-robust cousin (AUC 0.68);
  `sent_stdev` does **not** discriminate (AUC 0.516) and is no longer a verdict
  input. Until a human anchor exists, "toward/away from the human mean" is a
  direction, not a validated human-likeness verdict.
