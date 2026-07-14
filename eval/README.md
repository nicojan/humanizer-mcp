# Humanizer eval harness

Dev-only measurement tooling. **No API calls, no models, no network**: pure
deterministic Python plus the deployed checker (imported read-only). Never
modifies `src/` or the Docker image, and adds no third-party dependencies.
Implements Steps 0-2 of
`docs/superpowers/specs/2026-06-28-humanizer-eval-methodology-design.md`.
The Step-2 decision grid and its conclusion are recorded in `eval/FINDINGS.md`.

## Layers

- **L0: checker adherence** (`eval/scorers/l0_checker.py`): severity-weighted
  house-style compliance per 1k words. NOT a humanness detector: the rules ban
  things humans do (em-dashes), so human text trips it too.
- **Texture features** (`eval/scorers/texture.py`): deterministic human-vs-AI
  candidates: sentence-length burstiness, lexical diversity, n-gram repetition.
  No models. None trusted in isolation; the spike finds which (if any) discriminate.

## Step 0: signal spike (the gate)

```bash
python -m eval.spike       # pooled gate (pre-registered)
python -m eval.per_genre   # per-genre breakdown (diagnostic, not the gate)
```

For each texture feature, computes AUC over the human vs AI piles in
`eval/corpus/` (direction-agnostic: `max(auc, 1-auc)`). PASS = some feature
clears 0.75. The corpus is **16 human + 16 AI**, four genres balanced, built per
`docs/superpowers/specs/2026-06-29-humanizer-eval-corpus-construction.md`;
provenance and the recorded verdict live in `eval/corpus/SOURCES.md`. FAIL = the
cheap deterministic signal is too weak; then either accept a heavier local-model
signal, human-only rating, or keep the MCP as-is.

Current verdict (n=16 vs 16): **PASS**: `hapax_ratio = 0.82`. Lexical diversity,
not sentence burstiness, carries the signal; burstiness does not separate the
piles. See `SOURCES.md` for the full record.

## Step 1: minimal harness (offline scorer)

The harness does **not** generate text. Produce outputs yourself under each
condition (from the prompts in `eval/tasks.py`) and save them under a writer dir:

```
eval/outputs/<writer>/unaided/<id>.txt   # written with no humanization rules
eval/outputs/<writer>/rules/<id>.txt     # written with the rules applied
```

Then (`main()` reads the `primary` writer's slice):

```bash
python -m eval.harness
```

Prints L0 (compliance) and texture means per condition. Direction-only at this n.

## Step 2: decision grid (offline scorer)

Adds the `rules_loop` condition (write -> check -> fix via `run_checks`) and a
second writer. Layout: `eval/outputs/<writer>/<condition>/<id>.txt` for
conditions `unaided`, `rules`, `rules_loop`.

```bash
python -m eval.grid
```

Enforces the spec §6.3 anti-circularity split in how it reads results: judge
`unaided` vs `rules` on L0 adherence; judge `rules` vs `rules_loop` on
human-likeness texture only (the loop wins L0 by construction). The texture read
is distance to the *human mean* (a rising hapax is a move toward the AI side, not
toward human; corrected 2026-06-29, see `eval/reference.py`), with a length-robust
proxy (`mattr`) alongside hapax and burstiness excluded as non-discriminating.
Conclusion in `eval/FINDINGS.md`: reading the rules roughly halves violations and
the loop clears the rest to zero (the firm, adherence-only result); the loop is
**not** shown to improve human-likeness (its texture trends mildly toward the AI
side), so the MCP foregrounds the loop as primary usage for adherence
(`foundation.primary_usage`, v1.3.0).

## Tests

```bash
python -m pytest tests/eval/ -v
```
