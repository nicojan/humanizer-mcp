# Performative framing beat (self-aware flourish): rule design

**Date:** 2026-07-06
**Status:** Approved (design), implementing
**Origin:** In-the-wild reviewer feedback on prose that had passed the checker clean. Content run through mcp-humanizer retained a class of "performative" beats: sentences or labels whose job is to *perform* insight, closure, or self-awareness rather than carry content.

## The tell

A sentence or label whose real job is to signal "this is well-crafted" rather than say one more true, specific thing. Three recurring sub-forms:

1. **Self-satisfied closer**: a neat aphorism ending a section that sounds profound but adds no new fact, name, or number, often crediting the author or pivoting on a tidy antithesis (`public/private`, `X/mine`, `not-just-X-but-Y`).
2. **Meta label**: text that names the artifact's own format or length instead of its subject: "in 200 words", "in brief", "the short version", "at a high level", "to put it simply".
3. **Clever paradox headline**: a punchy inversion ("Everyone steers the learner but the learner") used to sound sharp; legitimate as a genuine title, a tell when it substitutes for a plain statement of the point.

**Why it's a tell:** these are moves that optimize for surface polish over content, and they are topic-agnostic: the same closer could end almost any essay.

**Caveat (definitional):** a single strong aphorism or a paradox title can be legitimate and human. The rule targets *repetition and substitution for content*, not the device itself. This is judgment, not a hard prohibition.

## Design decision

Split the tell across the two enforcement homes by mechanizability, mirroring how the codebase already separates deterministic tells (`banned_structures.json`) from judgment/texture checks (`self_review.json`):

- The **meta label** sub-form is partly mechanizable → a **narrow located detector** (`BS-022`), scoped so it fires *only* on a standalone label line/heading, never an embedded use.
- The **self-satisfied closer**, **first-person meta-commentary**, and **paradox-substitution** sub-forms are judgment → a **`manual_review` rubric item** in `self_review.json`.

**Entirely data-only.** The regex auto-wires through `loader.load_regex_structures` → `structures.find_regex_structures`; the rubric auto-wires through `loader.load_self_review`. No `src/` change, so it deploys by git-push + `docker restart mcp-humanizer` (no rebuild, no sudo), exactly like `BS-021`.

### Flagged points, resolved

- **Overlap with `BS-018` (`copula_maxim_closer`).** Kept distinct. `BS-018` remains the *mechanical* closer detector (paragraph-final short abstract-subject copula maxim). The rubric item owns the *judgment* closer forms `BS-018` cannot catch: crediting-the-author closers, first-person meta-commentary, paradox-substitution. **No new closer regex is added**: that is where false-positive risk lives.
- **"At a high level" / "to put it simply" false-positive risk.** Kept in the detector, guarded by a **terminal-only** constraint: the label must be the entire bounded line/sentence (optionally followed by one terminal punctuation mark, then line-end or string-end). The common embedded forms ("At a high level, the system does X." / "To put it simply, this works.") do not match, because a comma/clause follows the label instead of a boundary. Verified in tests.
- **`report.py` static fallback (`_MANUAL_REVIEW`) is intentionally NOT edited.** That list is already a loose, differently-worded snapshot (6 items vs the data file's 7, different wording), used only for direct `assemble_report` callers that pass `manual_review=None`. The deployed and tested path (`run_checks`) always reads `self_review.json`. Leaving it out of code keeps the change data-only.

## Components

### 1. `BS-022 meta_label`: `data/banned_structures.json`

- `method: regex`, `gate: checklist`, `confidence: low`, `source_examples: ["AP-035"]`.
- Fires only when a meta-label is the whole bounded line/heading. Leading boundary: string-start, newline, or sentence terminator + whitespace. Trailing boundary: optional horizontal whitespace, one optional terminal mark (`. : ! ?`), optional horizontal whitespace, then a lookahead for newline or string-end (so the required line break is not consumed, and multi-label blocks each match).
- Triggers (TL;DR deliberately excluded: common and acceptable in casual writing):
  - Length: `in \d+ words`
  - Brevity: `in brief`, `in short`, `the short version`, `the short of it`, `the gist`
  - Summary / altitude: `a quick summary`, `at a high level`, `to put it simply`
- `fix`: replace the format/length/brevity label with a phrase about the content itself, or cut it and let the section's content name it.

**Pattern (case-insensitive, no MULTILINE; `finditer` over full text):**

```
(?:^|\n|[.!?]\s+)(in\s+\d+\s+words|in\s+brief|in\s+short|the\s+short\s+version|the\s+short\s+of\s+it|the\s+gist|a\s+quick\s+summary|at\s+a\s+high\s+level|to\s+put\s+it\s+simply)[ \t]*[:.!?]?[ \t]*(?=\n|$)
```

### 2. `AP-035`: `data/anti_patterns.json`

Matching `AP-034`'s shape (`id`, `category`, `before`, `after`, `explanation`). `before: "in 200 words"` → `after: "the direction problem"`. Explanation ties it to `BS-022`: a meta label naming the artifact's format/length instead of its subject.

### 3. Rubric item: `data/self_review.json`

One new `manual_review` item, "Performative framing beat," covering the three judgment sub-forms with the definitional caveat (keep at most one aphoristic/paradox construction per piece, only where it does analytical work). Cross-refs `BS-018`, `BS-022`/`AP-035`, and `AP-033`.

### 4. `caveats.json`

A `performative_framing` core caveat: surface flourish is a low-ceiling tell; the device is human in moderation; flag as judgment, not prohibition. Consistent with `flow_over_surface_features` (content and flow beat surface polish).

## Testing

- `tests/checker/test_meta_label.py`:
  - Positive: each trigger group as a standalone label/heading matches `BS-022`.
  - False-positive guards: "At a high level, the system does X." and "I explained it in brief to the team." and "To put it simply, this works." do NOT match.
  - Boundary: a label mid-paragraph (not sentence-initial) does not match; a label followed by a blank line (`\n\n`) does match.
- `tests/checker/test_self_review.py` (or `test_pr2_additions.py`): pin the new rubric line's presence, mirroring the abstraction-as-agent pin.

## Propagation

- `CLAUDE.md`: a bullet documenting `BS-022` + the rubric item and their FP discipline.
- Sibling repo `humanize-text-prompt` mirrors these rules; sync after merge.
