# mcp-humanizer: Product Requirements Document

## Overview

`mcp-humanizer` is an MCP server that serves as the authoritative reference for Claude (via Claude.ai or Claude Code) when producing or revising written content to read as naturally human-authored. It encodes psycholinguistic, lexical, structural, and discourse-level patterns that distinguish human writing from AI-generated text, along with content-type-specific profiles and concrete before/after rewrite examples.

The server does **not** rewrite text itself. It provides rules, patterns, substitutions, and examples so that Claude can apply them during generation or revision.

## Role in the Ecosystem

- **`style-mcp`** owns brand voice, tone, and linguistic style for Human, an Education Collective
- **`mcp-humanizer`** owns the general-purpose "write like a human" ruleset: detector-aware patterns that apply regardless of brand
- When producing branded content, Claude should call **both** servers: `style-mcp` for voice/tone, `mcp-humanizer` for naturalness

## Goals

- Provide a single source of truth for all humanization rules across nine data dimensions
- Give Claude a composite endpoint (`get_humanize_guide`) that returns everything needed for a given content type in one call
- Encode concrete before/after anti-patterns so Claude can learn by example
- Support incremental refinement of rules via Git history on the source repo (updates flow via `git push` + container restart on the host)
- Document caveats (ESL considerations, detector brittleness, ethical boundaries)

## Non-Goals

- This server does **not** rewrite or generate text; Claude does that
- Brand voice and tone remain in `style-mcp`
- Student data remains in `students-mcp`
- Curriculum content remains in `curriculum-mcp`
- Slide-building instructions remain in `slides-mcp`

## Data Model

All data is stored as JSON files in the `/data` directory, tracked by Git.

| File | Description | Volatility |
|---|---|---|
| `foundation.json` | Absolute (non-negotiable) rules, core principle, two axes, priority hierarchy | Low |
| `lexical_patterns.json` | Flagged words, substitutions, vocabulary rules | Medium; refined as detectors evolve |
| `structural_patterns.json` | Sentence length, syntax, punctuation, POS targets | Medium |
| `sentiment_tone.json` | Neutral bias, emotional layering, subjectivity | Low |
| `discourse_cohesion.json` | Transitions, markers, cohesive devices, repetition | Low |
| `psycholinguistic_texture.json` | Cognitive load, self-monitoring, retrieval patterns | Low |
| `content_profiles.json` | Per-content-type adjustments (academic, marketing, tech, prose) | Medium; grows as new types are added |
| `anti_patterns.json` | Before/after examples of AI → human rewrites | High; grows continuously |
| `caveats.json` | ESL, detector brittleness, ethical considerations | Low |

## Tools

### Read Tools

| Tool | Description |
|---|---|
| `humanizer_get_guide` | **Full composite endpoint.** Returns foundation + all patterns + the matching content profile + caveats for a given content type. Use for major writing tasks. |
| `humanizer_get_summary` | **Lightweight composite.** Returns absolute_rules, core principle, priority hierarchy, and content profile. Use for quick edits. |
| `humanizer_get_foundation` | Returns absolute_rules, core principle, axes, and priority hierarchy |
| `humanizer_get_lexical_patterns` | Returns flagged words, substitutions, vocabulary rules |
| `humanizer_get_structural_patterns` | Returns sentence length, syntax, punctuation, POS targets |
| `humanizer_get_sentiment_tone` | Returns neutral bias, emotional layering, subjectivity rules |
| `humanizer_get_discourse_cohesion` | Returns transitions, markers, cohesive devices, repetition rules |
| `humanizer_get_psycholinguistic_texture` | Returns cognitive load, self-monitoring, retrieval patterns |
| `humanizer_get_content_profile` | Returns adjustments for a specific content type (academic, marketing, tech, prose, or all) |
| `humanizer_get_anti_patterns` | Returns before/after rewrite examples, optionally filtered by category |
| `humanizer_get_caveats` | Returns ESL considerations, detector brittleness notes, ethical boundaries |

### Write Tools

None. This is a public read-only MCP. Data updates flow via `git push` to the source repo + container restart on the host (the entrypoint pulls the latest `data/` from GitHub on startup). There is no runtime write surface and no auth token.

## Security

- Read tools are unauthenticated; anyone can connect and use the humanization rules. This is intentional; the server is a public reference system.
- No write tools exist in the deployed binary. Mutation code is not present at runtime; this is a non-negotiable rule for public MCPs in this ecosystem.
- No Cloudflare Access policy is applied; the server is publicly reachable by design.
- Every request is logged to stdout with the `CF-Connecting-IP` header so the access trail is visible in `docker logs`.

## Shared Endpoints (Cross-Server)

| Tool | Intended Consumers | Description |
|---|---|---|
| `humanizer_get_guide` | Any server or agent producing written content | Returns the full humanization ruleset for a content type |
| `humanizer_get_anti_patterns` | Any server needing rewrite examples | Returns before/after pairs for learning |

## Technical Specification

| Parameter | Value |
|---|---|
| Language | Python |
| Framework | FastMCP (official MCP Python SDK, `mcp` package) |
| Storage | JSON files in Git-tracked `/data` directory |
| Transport | Streamable HTTP |
| Auth | None; public read-only |
| Container | Docker + docker-compose.yml |
| Host | Any container host; single stateless container behind a reverse proxy or tunnel |
| Port | 8016 (configurable via `PORT`) |
| Public host | Set via `PUBLIC_HOST` |

## Open Items

- Content profiles may expand beyond the initial four types (academic, marketing, tech, prose)
- Anti-patterns collection grows by editing `data/anti_patterns.json` in this repo and pushing; the host then restarts the container, which pulls the latest data on entrypoint
- DNS rebinding protection is currently disabled for cloudflared compatibility; tightening to a `Host` allowlist is a deferred follow-up (see `src/server.py`)
