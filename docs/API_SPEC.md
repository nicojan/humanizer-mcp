# mcp-humanizer: API Specification

All tool names are prefixed with `humanizer_` to avoid conflicts with other MCP servers.
All read tools accept an optional `response_format` parameter (`json` or `markdown`, default: `json`).
All responses have `meta` blocks stripped and use compact JSON for token efficiency.

## Read Tools

### `humanizer_get_guide`

**Full composite endpoint.** Returns all nine data dimensions for a given content type with meta blocks stripped. Use only for major writing tasks or full rewrites.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `content_type` | string | No | One of: `academic`, `marketing`, `tech`, `prose`. Defaults to `prose`. |
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Compact JSON containing all data dimensions (foundation, lexical_patterns, structural_patterns, sentiment_tone, discourse_cohesion, psycholinguistic_texture, content_profile, anti_patterns, caveats), all meta-stripped.

**Error handling:**
- If `content_type` is provided but not found in profiles, return all profiles with a warning note.

---

### `humanizer_get_summary`

**Lightweight composite endpoint.** Returns core principle, priority hierarchy, section-level variation, and content profile. Use for quick edits and revision passes.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `content_type` | string | No | One of: `academic`, `marketing`, `tech`, `prose`. Defaults to `prose`. |
| `response_format` | string | No | `json` (compact, default) or `markdown` (human-readable). |

**Returns:** Compact JSON with core_principle, two_axes, priority_hierarchy, section_level_variation, and content_profile.

---

### `humanizer_get_foundation`

Returns core principle, axes, and priority hierarchy.

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
| `content_type` | string | No | One of: `academic`, `marketing`, `tech`, `prose`, or `all`. Defaults to `all`. |
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

**Deterministic compliance checker.** Analyzes candidate text and returns a compliance report. No LLM; read-only with respect to server state; does not log input text. Run after revising, then fix and re-run until `prohibitions_clear`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Candidate text to check (1-100000 chars). |
| `content_type` | string | No | Tunes the burstiness target: `academic`, `marketing`, `tech`, `prose` (default). |

**Returns:** Compact JSON: `prohibitions_clear` (bool, true iff no hard violations), `note`, `hard_violations[]` (em-dashes, stacked punctuation marks, and fixed AI phrases, with offsets), `must_clear[]` (located findings to rewrite or justify: flagged terms; regex/heuristic banned structures (the `BS-*` tells); rule-of-three density; cross-section uniformity (`segment_uniformity`); reality-assertion density (`credibility_insistence`); low burstiness; and punctuation issues (missing terminal marks, run-on spans, comma splices)), `metrics` (burstiness stats plus `segment_variation`), `manual_review[]` (the human-likeness **self-review rubric** the calling model runs against its own draft: rhythm, reused rhetorical shape, section-to-section variation, generic competence/stance, abstraction-as-agent; the texture checks the server cannot verify; data-driven from `data/self_review.json`), `next_action` (sequences the self-review step after the mechanical fixes).

---

## Write Tools

None. mcp-humanizer is a public read-only MCP. Updates to rule data flow via `git push` to this repo plus a container restart on the host; there is no runtime write surface and no auth token.
