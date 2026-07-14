# Humanizer Eval: Step 0 Calibration Corpus Construction

**Date:** 2026-06-29
**Status:** Approved for implementation
**Author:** Nico Jan (design by Claude)
**Parent spec:** `docs/superpowers/specs/2026-06-28-humanizer-eval-methodology-design.md`

## Purpose

Build the Step 0 calibration corpus, "obvious" known-human vs. known-AI text,
so the signal spike (`python3 -m eval.spike`) tests the texture features against a
real ≥15+15 pile instead of the 2+2 smoke-test seed. The whole point of Step 0 is
**validity**: does the spike separate human from AI on *human-vs-AI texture*, or on
a confound? Every decision below exists to close a confound.

## Counts & genre balance

- **16 human / 16 AI**, four genres × four each (>15 bar; balanced so genre cannot
  dominate the pooled AUC).
- Genres mirror the benchmark tasks in `eval/tasks.py`: `prose` (personal
  anecdote/essay), `technical` (how-to intro), `cover_letter`, `marketing`
  (product blurb).
- Plus documented, empty slots in the manifest for other-model AI samples the
  maintainer adds later (true multi-model diversity).

## Validity guards (the loopholes this corpus must not fall into)

1. **Modern register only (human pile: ~2010 to 2022-11-29).** No archaic
   public-domain prose. Pre-ChatGPT guarantees the text is genuinely human; a
   *modern* register guarantees the spike measures human-vs-AI texture, not era /
   period vocabulary.
2. **Length-matched pairs (±15%).** `sentence_length_stdev`, `_range`,
   `type_token_ratio`, and `hapax_ratio` all move with length. Each AI sample is
   generated to within ±15% of its paired human sample's word count. Target band
   ~120-180 words; every sample ≥5 sentences (so stdev is meaningful).
3. **Naive AI generation.** The AI pile is produced by a clean subagent given only
   `genre + topic + target word count`, never the human text, never any mention
   of the humanizer rules. This avoids the circularity of the rule-aware model
   dodging or exaggerating the exact tells the rules target. Raw, default-voice,
   un-humanized output.
4. **Blind, pre-registered selection.** Human samples are chosen by a fixed
   source/genre rule decided before scoring, never filtered or cherry-picked on
   their texture scores. The 0.75 AUC bar in `eval/spike.py` is pre-registered and
   unchanged.
5. **Frozen provenance.** Every human sample cites an *archived* source with a
   verifiable timestamp (Wikipedia `oldid` + revision date, or a Wayback capture
   URL + capture date) so "published before ChatGPT" is provable from the manifest
   alone, not a live URL that can change.
6. **Per-genre diagnostic.** Report per-genre AUC alongside the pooled gate so one
   highly-separable genre cannot mask a flat one. Pooled AUC vs 0.75 remains the
   pre-registered gate; per-genre is visibility only.

## Human sourcing plan (Hybrid: open-licensed where a genre allows; reputable excerpts where it doesn't)

| Genre | Source rule | License posture |
|---|---|---|
| `technical` | Wikipedia *old revisions* (oldid, pre-2022) + official docs (Python/Django/MDN) archived snapshots | Open (CC-BY-SA / docs licenses) |
| `prose` | Reputable dated essays/blogs, 2010-2022, via Wayback snapshot (e.g. Paul Graham) | Excerpt + attribution |
| `cover_letter` | Archived .edu career-center samples (Purdue OWL, Harvard OCS, university career centers) via Wayback | Excerpt + attribution |
| `marketing` | Pre-2022 archived product/brand pages from reputable companies via Wayback | Excerpt + attribution |

Excerpts kept to the minimum the feature needs (~120-180 words). Any source whose
pre-ChatGPT date cannot be confirmed from a frozen snapshot is dropped, not guessed.

## On-disk format

- `eval/corpus/{human,ai}/<genre>_NN.txt`: **sample text only**. `load_pile`
  scores the entire file verbatim, so no inline metadata, headers, or source lines
  (they would corrupt burstiness/lexical scores).
- `eval/corpus/SOURCES.md`: the manifest. One row per file:
  `filename | genre | source | archived URL | publish/capture date | license | excerpt? | word count`.
- The four synthetic seed files (`sample_human_*`, `sample_ai_*`) are removed:
  fabricated text must not sit in a "genuine human / raw AI" pile.

## Success criteria

- 16+16 corpus committed, every human sample with a frozen pre-2022-11-30 citation
  in `SOURCES.md`.
- `python3 -m eval.spike` re-run against the real corpus; the verdict (pooled AUC
  vs 0.75, plus per-genre diagnostic) recorded.
- `eval/README.md` updated to reflect the real n (drop the "2+2 smoke test" caveat).
- `tests/eval/` still green.
