# BS-021 `noun_participle_fragment`: design

**Date:** 2026-07-03
**Status:** approved
**Trigger:** In-the-wild review of prose that had passed `humanizer_check_text` clean. A reviewer flagged `"The same board, rebuilt."`, *"exactly the 'Noun, past-participle.' construction that reads as AI copy."* The June checker had no detector for it.

## The tell

A sentence that is *only* a determiner-led noun phrase, a comma, and a trailing past
participle, with **no finite verb**:

- `The same board, rebuilt.`
- `The homepage, reimagined.`
- `The whole system, rewritten.`

It is a verbless flourish standing in for a real sentence. It is the past-participle
sibling of `BS-005 participle_tail` (which catches the *present*-participle `, contributing…`
tail) and a fragment cousin of the antithesis family (BS-011/BS-013).

## Decision

Implement as a **regex `banned_structure`** (`gate: checklist`, `confidence: low`), not a
heuristic. Rationale:

- It slots into the existing `load_regex_structures()` → `find_regex_structures()` path with
  **no new code**: the same mechanism as BS-002…BS-019.
- Because it is pure data, it deploys **data-only**: merge to `main`, then
  `docker restart mcp-humanizer` on the host (the entrypoint git-pulls `data/`). No image
  rebuild, no `sudo`.
- The fragment nature is enforced *structurally* by the pattern (see below), so a heuristic
  buys no extra correctness here, only more false-positive surface.

`gate: checklist` (never `hard`), matching every research-backed structural tell: a stylistic
call the calling model rewrites or justifies, never a hard block on `prohibitions_clear`.

## Pattern and false-positive discipline

```
(?:^|[.!?]\s+)
(?:the|a|an|this|that|these|those|its|their|his|her|our|my|your)\s+
(?:[a-z]+\s+){0,2}[a-z]+,\s+
(?:<irregular participles>|[a-z]{3,}ed)
[.!?]
```

Three guards keep the false-positive rate near zero, consistent with the checker's standing
discipline:

1. **Sentence-initial determiner** (`(?:^|[.!?]\s+)` + article/possessive/demonstrative).
   Skips `"He left the room, defeated."` (a legitimate depiction, not the tell) because
   `the room` is not sentence-initial.
2. **Participle is the last token** (immediately followed by terminal punctuation). Bounding
   the whole sentence to `Det … noun, participle.` leaves no room for a finite verb, so it
   fires **only** on the verbless fragment. Skips `"The board, which we rebuilt, is live."`
   and `"The report, revised, was sent."` (participle followed by a comma, more clause after)
   and `"The summit, held annually."` (participle has a tail).
3. **`[a-z]{3,}ed` floor** for regular participles: requires ≥5 letters, so short
   look-alikes `red` / `bed` / `wed` / `shed` do not match (`"The wall, red."` stays quiet).
   Irregulars that do not end in `-ed` (`rebuilt`, `rewritten`, `remade`, `reborn`, `redone`,
   `rethought`, `undone`, `built`, `made`, `done`, `written`, `born`, `torn`, `worn`, `drawn`,
   `grown`, `known`, `shown`, `thrown`) are listed explicitly.

Idioms without the comma (`"Case closed."`, `"Mission accomplished."`) never match; the comma
is definitional to this construction and is what separates the tell from fixed expressions.

## Architecture fit

- **`data/banned_structures.json`**: new `BS-021` entry (regex, checklist, low), auto-wired.
- **`data/anti_patterns.json`**: new `AP-034` (structural, before/after) so BS-021's
  `source_examples` cites a real anti-pattern, preserving the "consolidated from
  anti_patterns.json" invariant every `BS-*` follows.
- **`tests/checker/test_noun_participle_fragment.py`**: positive cases + the three FP guards.
- **Docs**: `CLAUDE.md` rule-log bullet (2026-07-03) and this spec.

## Deploy

Data-only. `docker restart mcp-humanizer` on the host; verify the served
`banned_structures.json` in-container and end-to-end via the live `humanizer_check_text` tool.
