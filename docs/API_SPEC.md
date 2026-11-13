# mcp-humanizer: API Specification

All tool names are prefixed with `humanizer_` to avoid conflicts with other MCP servers.
All read tools accept an optional `response_format` parameter (`json` or `markdown`, default: `json`).
All responses have `meta` blocks stripped and use compact JSON for token efficiency.

## Read Tools

### `humanizer_get_guide`

**Full composite endpoint.** Returns all nine data dimensions for a given content type with meta blocks stripped. Use only for major writing tasks or full rewrites. The full payload is about 40k tokens (roughly 157k characters for prose), over some clients' tool-output cap. Registered with `meta={"anthropic/maxResultSizeChars": 80000}`, so every page (`core` is about 63k characters at most) arrives inline in Claude Code and the full guide lands in a file.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `content_type` | string | No | One of: `academic`, `marketing`, `tech`, `prose`, `creative`, `case_study` (aliases `portfolio`, `product`), `resume` (aliases `résumé`, `cv`). Defaults to `prose`. |
| `part` | string | No | One of `core`, `lexical`, `anti_patterns`, `caveats`, or `all` (default). Pages the guide for clients that cap tool output: `core` bundles foundation, content profile, structure, texture, cohesion, tone and verification (each page stays under 75k characters); fetch `lexical`, `anti_patterns` and `caveats` after it. Each page's response names the pages still to fetch in `guide_parts_remaining`. Omit, or pass `all`, for the full payload in one call. |
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Compact JSON containing all data dimensions (foundation, lexical_patterns, structural_patterns, sentiment_tone, discourse_cohesion, psycholinguistic_texture, content_profile, anti_patterns, caveats), all meta-stripped, or one page of them when `part` is given.

**Error handling:**
- If `content_type` is provided but not found in profiles, return the `general_prose` profile with a `_warning` naming the valid types. (Before 2026-11-09 it returned every profile, which put `core` over the 75k cap once there were seven.)
- If `part` is not one of the recognized values, the call errors rather than silently returning the full payload.

---

### `humanizer_get_summary`

**Lightweight composite endpoint.** Returns the absolute rules, the enforcement block, core principle, priority hierarchy, the `uniform_application_paradox` caveat and a compact content profile. Use for quick edits and revision passes.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `content_type` | string | No | One of: `academic`, `marketing`, `tech`, `prose`, `creative`, `case_study` (aliases `portfolio`, `product`), `resume` (aliases `résumé`, `cv`). Defaults to `prose`. |
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Compact JSON with absolute_rules, enforcement, core_principle, priority_hierarchy, content_profile and uniform_application_paradox.

---

### `humanizer_get_foundation`

Returns the absolute rules, enforcement, primary usage, core principle, axes and priority hierarchy. Section-to-section variation is not here; it lives in `structural_patterns.cross_segment_variation`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Contents of `foundation.json` with meta stripped, excluding `application_protocol` (call `humanizer_get_application_protocol` for the phase plan).

---

### `humanizer_get_lexical_patterns`

Returns flagged words, substitutions, and vocabulary rules.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `risk_level` | string | No | Filter by `high`, `medium`, or `low`. Returns all if omitted. |
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Contents of `lexical_patterns.json` with meta stripped, optionally filtered.

---

### `humanizer_get_structural_patterns`

Returns sentence length targets, syntax rules, punctuation rules, and POS targets.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Contents of `structural_patterns.json` with meta stripped.

---

### `humanizer_get_sentiment_tone`

Returns neutral bias rules, emotional layering techniques, and subjectivity guidance.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Contents of `sentiment_tone.json` with meta stripped.

---

### `humanizer_get_discourse_cohesion`

Returns transition rules, discourse markers, cohesive devices, and repetition guidance.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Contents of `discourse_cohesion.json` with meta stripped.

---

### `humanizer_get_psycholinguistic_texture`

Returns cognitive load markers, self-monitoring patterns, and retrieval cues.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Contents of `psycholinguistic_texture.json` with meta stripped.

---

### `humanizer_get_content_profile`

Returns per-content-type adjustments.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `content_type` | string | No | One of: `academic`, `marketing`, `tech`, `prose`, `creative`, `case_study`/`portfolio`, `resume`/`cv`, or `all`. Defaults to `all`. |
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** The matching profile object, or all profiles if `all` or omitted.

**Error handling:**
- If `content_type` is not found, return all profiles with a warning.

---

### `humanizer_get_anti_patterns`

Returns before/after rewrite examples.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `category` | string | No | Filter by category (e.g., `lexical`, `structural`, `sentiment`, `discourse`, `psycholinguistic`). Returns all if omitted. |
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Array of anti-pattern examples, optionally filtered by category.

---

### `humanizer_get_caveats`

Returns ESL considerations, detector brittleness notes, and ethical boundaries.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Contents of `caveats.json` with meta stripped.

---

### `humanizer_check_text`

**Deterministic compliance checker.** Analyzes candidate text and returns a compliance report. No LLM; read-only with respect to server state; does not log input text. Run after revising. Resolve every hard violation; for each `must_clear` item, rewrite only the flagged span or justify it, and stop after two fix rounds; a hard violation is never justified, so keep fixing until `prohibitions_clear` is true. Make the last check on the assembled document with `rubric="full"`, do the self-review, and if it changed anything, check once more and confirm `prohibitions_clear`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Candidate text to check (1-100000 chars). |
| `content_type` | string | No | Content type: `academic`, `marketing`, `tech`/`technical`, or `prose` (default). Pass `label` or `notes` for headings, worksheet cells, UI strings or CEFR-pitched copy: sentence-length numbers are still shown in `metrics` with `length_metrics_apply: false`, and `segment_variation.uniformity_flag` reads false so `segment_uniformity` is not listed in `must_clear`. Every other layer runs unchanged. `resume` (also `résumé`, `cv`; added 2026-11-09) does the same and also skips `rule_of_three_density`, because a Skills block is a list. `case_study` runs exactly as `prose`; its guidance is served by `humanizer_get_content_profile`. In every content type, a flagged term inside an entry of `lexical_patterns.terms_of_art` ("differentiated instruction") is not reported. The report's `manual_review` is filtered by `content_type`; with none, or an unknown one, every rubric item is sent. |
| `rubric` | string | No | `short` (default) or `full`. Selects what `manual_review` carries: one short line per self-review item for the content type, or each item's full text. The loop runs on `short`; the model makes one last call on the assembled document with `full` and does the self-review against its draft. Any other value is a validation error. |

**Returns:** Compact JSON: `prohibitions_clear` (bool, true iff no hard violations), `note`, `hard_violations[]` (em-dashes, stacked punctuation marks, and fixed AI phrases, with offsets; the em-dash check covers U+2014 and the `--` digraph, but skips hyphen runs on a line made only of `-`, `|`, `:` and spaces, so markdown table separators, horizontal rules, setext underlines and front-matter fences do not block `prohibitions_clear`; it also skips a `--` that is a lowercase command-line flag (`--verbose`, `--save-dev`, preceded by whitespace, the start of the text, a backtick, `(`, or a quote when the flag runs straight to the closing quote) and any `--` inside a closed fenced code block or an inline code span; U+2014 fires everywhere, code included, and a capitalised lead such as an attribution, a `--Dana` sign-off or `--No, I said.` fires; a dash glued to a quote and followed by more words, such as a quoted `--and when`, fires too, and an unclosed fence hides nothing), `must_clear[]` (located findings to rewrite or justify: flagged terms; regex/heuristic banned structures (the `BS-*` tells); document-budget overruns for structures that carry a `document_budget` and appear more often than it in the text supplied; rule-of-three density; cross-section uniformity (`segment_uniformity`); reality-assertion density (`credibility_insistence`); and punctuation issues (missing terminal marks, run-on spans, comma splices)), `metrics` (raw sentence-length numbers, `length_metrics_apply` and `segment_variation`; sentence-length variance is reported as a number, never as a finding or a target, and the former `burstiness_flag` and `burstiness_target_stdev` keys are gone), `manual_review[]` (the human-likeness **self-review rubric** the calling model runs against its own draft, the texture checks the server cannot verify; data-driven from `data/self_review.json`, filtered by `content_type`, as short lines by default or full texts with `rubric="full"`), `next_action` (rewrite only flagged spans, stop after two fix rounds on `must_clear` items while a hard violation is fixed until `prohibitions_clear` is true, then one last check on the assembled document with `rubric="full"` and the self-review, and one more check confirming `prohibitions_clear` if the self-review changed anything).

---

## Write Tools

None. mcp-humanizer is a public read-only MCP. Updates to rule data flow via `git push` to this repo plus a container restart on the host; there is no runtime write surface and no auth token.
