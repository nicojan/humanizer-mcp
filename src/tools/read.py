"""Read-only tools for mcp-humanizer."""

import json
import logging
from typing import Any, Literal, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from src.storage.json_store import load_json

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared types & helpers
# ---------------------------------------------------------------------------

CONTENT_TYPE_ALIASES = {
    "prose": "general_prose",
    "general_prose": "general_prose",
    "general": "general_prose",
    "tech": "technical",
    "technical": "technical",
    "academic": "academic",
    "marketing": "marketing",
}


def _resolve_content_type(ct: str, profiles: dict) -> str:
    """Resolve a content type string to a key that exists in profiles."""
    if ct in profiles:
        return ct
    canonical = CONTENT_TYPE_ALIASES.get(ct.lower())
    if canonical and canonical in profiles:
        return canonical
    return ct


_ESSENTIAL_META_KEYS = ("usage", "application_rule")
# Provenance/justification-only keys dropped from every served payload. Both
# are citation/exposition trails for data-file editors that add no signal to an
# LLM mid-rewrite: `research_basis` is a citation list; `theory` is the
# academic rationale paragraph behind a layer (the actionable content lives in
# sibling rules/markers/guidance). NOTE: `notes` is deliberately NOT here — in
# content_profiles.json the per-layer `notes` are the actionable payload.
_DROP_KEYS = frozenset({"research_basis", "theory"})


def _drop_keys(obj: Any) -> Any:
    """Recursively drop provenance-only keys (research_basis, theory) anywhere
    in the payload — including nested locations like
    structural_patterns.pos_distribution_targets.research_basis or
    psycholinguistic_texture.cognitive_load_artifacts.theory. They are citation
    and rationale trails for data-file editors and add no signal to an LLM
    mid-rewrite."""
    if isinstance(obj, dict):
        return {k: _drop_keys(v) for k, v in obj.items() if k not in _DROP_KEYS}
    if isinstance(obj, list):
        return [_drop_keys(x) for x in obj]
    return obj


def _strip_meta(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of data with the 'meta' key stripped to save tokens, but
    preserve the essential meta keys (usage, application_rule) as top-level
    fields on the result. Also applies _drop_keys recursively to remove
    field-level provenance (research_basis) wherever it appears outside meta."""
    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
    result = {k: _drop_keys(v) for k, v in data.items() if k != "meta"}
    for key in _ESSENTIAL_META_KEYS:
        if key in meta:
            result[key] = _drop_keys(meta[key])
    return result


def _compact_json(obj: Any) -> str:
    """Serialize to compact JSON (no indentation) to minimize token usage."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def _resolve_profile(
    content_type: Optional[str],
    profiles: dict,
) -> tuple[dict[str, Any], Optional[str]]:
    """Resolve a content profile. Returns (profile_data, warning_or_none)."""
    ct = _resolve_content_type(content_type or "prose", profiles)
    if ct in profiles:
        return profiles[ct], None
    return profiles, (
        f"Content type '{content_type}' not found. "
        f"Available: {list(profiles.keys())}. Returning all."
    )


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------

class ContentTypeInput(BaseModel):
    """Input for tools that accept an optional content type."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content_type: Optional[str] = Field(
        default=None,
        description=(
            "Content type to tailor rules for. One of 'academic', 'marketing', "
            "'tech'/'technical', 'prose'/'general_prose'. Defaults to 'prose'."
        ),
    )


class GuideInput(BaseModel):
    """Input for humanizer_get_guide."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content_type: Optional[str] = Field(
        default=None,
        description=(
            "Content type to tailor rules for. One of 'academic', 'marketing', "
            "'tech'/'technical', 'prose'/'general_prose'. Defaults to 'prose'."
        ),
    )
    part: Optional[Literal["core", "lexical", "anti_patterns", "caveats", "all"]] = Field(
        default=None,
        description=(
            "Page of the guide to return. The full guide is about 40k tokens, "
            "over some clients' tool-output limit, so fetch 'core' (foundation, "
            "content profile, structure, texture, cohesion, tone, verification), "
            "then 'lexical', 'anti_patterns' and 'caveats'. Omit, or pass 'all', "
            "for the full payload in one call."
        ),
    )


class RiskLevelInput(BaseModel):
    """Input for lexical patterns with optional severity filter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    risk_level: Optional[str] = Field(
        default=None,
        description=(
            "Filter by severity: 'high', 'moderate', or 'low'. 'medium' is "
            "accepted as a synonym for 'moderate'. Returns all if omitted."
        ),
    )


class CategoryFilterInput(BaseModel):
    """Input for anti-patterns with optional category filter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    category: Optional[str] = Field(
        default=None,
        description=(
            "Filter by category: 'lexical', 'structural', 'sentiment', "
            "'discourse', 'psycholinguistic'. Returns all if omitted."
        ),
    )


class ContentProfileInput(BaseModel):
    """Input for content profile tool."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content_type: Optional[str] = Field(
        default=None,
        description=(
            "One of 'academic', 'marketing', 'tech'/'technical', "
            "'prose'/'general_prose', or 'all'. Defaults to 'all'."
        ),
    )


# ---------------------------------------------------------------------------
# Payload builder (module-level — testable without FastMCP)
# ---------------------------------------------------------------------------

def build_foundation_payload() -> dict[str, Any]:
    """Foundation payload for humanizer_get_foundation: absolute_rules,
    enforcement, core principle, two axes, priority hierarchy, and
    section_level_variation — meta and provenance stripped.

    The application_protocol is intentionally excluded. It has its own tool
    (humanizer_get_application_protocol), and the 'minimum viable' usage mode
    this tool serves was only ever documented to carry the absolute rules,
    core principle, axes, and hierarchy. Excluding the ~1,950-token traversal
    map here stops it from double-shipping on every foundation (and lightest-
    touch) call; clients that want the phase plan call the protocol tool."""
    data = _strip_meta(load_json("foundation.json"))
    data.pop("application_protocol", None)
    return data


def build_guide_payload(content_type: Optional[str]) -> dict[str, Any]:
    """Assemble the full guide payload: all dimensions, ordered framing, and
    the verification loop instruction. Additive — existing keys are preserved."""
    files = [
        ("foundation", "foundation.json"),
        ("lexical_patterns", "lexical_patterns.json"),
        ("structural_patterns", "structural_patterns.json"),
        ("sentiment_tone", "sentiment_tone.json"),
        ("discourse_cohesion", "discourse_cohesion.json"),
        ("psycholinguistic_texture", "psycholinguistic_texture.json"),
        ("anti_patterns", "anti_patterns.json"),
        ("caveats", "caveats.json"),
    ]
    result: dict[str, Any] = {key: _strip_meta(load_json(fname)) for key, fname in files}
    result["foundation"].pop("ecosystem_workflow", None)

    profiles = _drop_keys(load_json("content_profiles.json").get("profiles", {}))
    profile, warning = _resolve_profile(content_type, profiles)
    result["content_profile"] = profile
    if warning:
        result["_warning"] = warning

    # Per-phase guidance lives in foundation.application_protocol.phases[]
    # (already included in result["foundation"]); restating it here would
    # duplicate ~250 tokens per call.
    result["verification"] = {
        "tool": "humanizer_check_text",
        "instruction": (
            "After revising, call humanizer_check_text with your output. Resolve "
            "every hard_violation, rewrite or justify each must_clear item, and "
            "re-run until prohibitions_clear is true. Then self-attest "
            "manual_review before returning."
        ),
    }
    return result


# Pages of the guide, in reading order. Each one stays under 75k characters,
# which fits a 25k-token tool-output cap even at a dense 3 characters a token;
# the full payload (about 166k characters for prose) does not.
GUIDE_PARTS: dict[str, tuple[str, ...]] = {
    "core": (
        "foundation",
        "content_profile",
        "structural_patterns",
        "psycholinguistic_texture",
        "discourse_cohesion",
        "sentiment_tone",
        "verification",
        "_warning",
    ),
    "lexical": ("lexical_patterns",),
    "anti_patterns": ("anti_patterns",),
    "caveats": ("caveats",),
}


def build_guide_part(content_type: Optional[str], part: Optional[str]) -> dict[str, Any]:
    """One page of the guide, or the full payload for None / 'all'."""
    full = build_guide_payload(content_type)
    if part in (None, "all"):
        return full
    if part not in GUIDE_PARTS:
        raise ValueError(f"unknown guide part {part!r}; use one of {sorted(GUIDE_PARTS)} or 'all'")
    order = list(GUIDE_PARTS)
    page = {key: full[key] for key in GUIDE_PARTS[part] if key in full}
    return {
        **page,
        "guide_part": part,
        "guide_parts_remaining": order[order.index(part) + 1:],
    }


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_read_tools(mcp: FastMCP) -> None:
    """Register all read-only tools with the MCP server."""

    # -- Composite endpoints ------------------------------------------------

    @mcp.tool(
        name="humanizer_get_summary",
        annotations={
            "title": "Get Humanization Summary",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_summary(params: ContentTypeInput) -> str:
        """Lightweight entry point. Returns absolute_rules, the core principle,
        priority hierarchy, the uniform_application_paradox caveat (the single
        most load-bearing warning), and a compact content_profile. Use for
        quick edits, revision passes, or orientation before pulling a full
        layer.

        For major writing tasks, use humanizer_get_guide instead.
        For single-dimension fixes, call the specific layer tool directly.

        Args:
            params: ContentTypeInput with optional content_type.

        Returns:
            str: JSON with absolute_rules, core_principle, priority_hierarchy,
            uniform_application_paradox, and a compact content_profile (label,
            perplexity_target, burstiness_target, layer_aggressiveness). The
            content_profile key matches humanizer_get_guide; the value here is
            a slim summary, there the full profile.
        """
        foundation = _strip_meta(load_json("foundation.json"))
        profiles = load_json("content_profiles.json").get("profiles", {})
        profile, warning = _resolve_profile(params.content_type, profiles)

        hierarchy = [
            {"order": h["order"], "layer": h["layer"], "action": h["action"]}
            for h in foundation.get("priority_hierarchy", [])
        ]

        profile_summary: dict[str, Any] = {}
        if isinstance(profile, dict) and "label" in profile:
            adjustments = profile.get("layer_adjustments", {})
            profile_summary = {
                "label": profile.get("label", ""),
                "perplexity_target": profile.get("perplexity_target", ""),
                "burstiness_target": profile.get("burstiness_target", ""),
                "layer_aggressiveness": {
                    layer: adj.get("aggressiveness", "")
                    for layer, adj in adjustments.items()
                },
            }

        # Surface the single most-important caveat in the summary so callers
        # who only fetch the summary still get the load-bearing warning.
        # Per the 2026-05-20 rule-set audit and caveats.json's own framing.
        uniform_paradox = None
        caveats_data = load_json("caveats.json")
        for caveat in caveats_data.get("core_caveats", []):
            if caveat.get("id") == "uniform_application_paradox":
                uniform_paradox = caveat
                break

        result: dict[str, Any] = {
            "absolute_rules": foundation.get("absolute_rules", {}),
            # Include the enforcement block so summary callers receive the
            # two-tier framing — zero_tolerance vs non-uniformity scope — which
            # tells the LLM that AR-002/AR-003 are never subject to "don't
            # apply uniformly" relaxation. Without this, the absolute_rules
            # block above can read as advisory.
            "enforcement": foundation.get("enforcement", {}),
            "core_principle": foundation.get("core_principle", {}).get("statement", ""),
            "priority_hierarchy": hierarchy,
            "content_profile": profile_summary,
        }
        if uniform_paradox is not None:
            result["uniform_application_paradox"] = uniform_paradox
        if warning:
            result["_warning"] = warning

        return _compact_json(result)

    @mcp.tool(
        name="humanizer_get_guide",
        annotations={
            "title": "Get Full Humanization Guide",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_guide(params: GuideInput) -> str:
        """Full composite endpoint — returns ALL data dimensions for a content type
        with meta blocks stripped for token efficiency. Use only for major writing
        tasks, new articles, or full rewrites. The whole guide is about 40k
        tokens; if your client caps tool output, page it with part='core', then
        'lexical', 'anti_patterns' and 'caveats' (each page names the ones still
        to fetch).

        For quick edits, use humanizer_get_summary.
        For single-dimension fixes, call the specific layer tool.

        Args:
            params: GuideInput with optional content_type and part.

        Returns:
            str: All data dimensions assembled for the task, meta-stripped, or
            one page of them when part is given.
        """
        return _compact_json(build_guide_part(params.content_type, params.part))

    # -- Single-layer endpoints ---------------------------------------------

    @mcp.tool(
        name="humanizer_get_application_protocol",
        annotations={
            "title": "Get Application Protocol",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_application_protocol() -> str:
        """Returns the ordered traversal that visits every rule path in the
        data set. Use this when starting a rewrite to plan a complete pass.
        Each phase names the tool to call, the JSON rule_paths the LLM must
        consider within that tool's payload, and a stop_condition that
        defines when the phase is complete.

        Walking this protocol guarantees coverage of every rule in the rule
        set. Coverage does NOT mean uniform application — see the
        uniformity_directive in the response, which mirrors
        caveats.uniform_application_paradox: every rule visited must be
        considered, but applying every rule is itself an AI signal.

        Returns:
            str: The application_protocol object: description,
            uniformity_directive, coverage_invariant, and the ordered
            phases[] array.
        """
        foundation = load_json("foundation.json")
        protocol = foundation.get("application_protocol", {})
        return _compact_json(protocol)

    @mcp.tool(
        name="humanizer_get_foundation",
        annotations={
            "title": "Get Foundation Principles",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_foundation() -> str:
        """Returns the foundation payload: absolute_rules (AR-001 preserve
        meaning, AR-002 em-dash ban, AR-003 punctuation correctness), the
        enforcement block (Tier-1 zero_tolerance members and verification
        instructions), the core principle, two analytical axes (perplexity
        and burstiness), the priority hierarchy, and section_level_variation.
        Lightest-weight tool that still carries the Tier-1 prohibitions; use
        this when an LLM only needs the non-negotiables.

        The ordered phase plan (application_protocol) is NOT included here to
        keep this payload minimal — call humanizer_get_application_protocol for
        the full traversal map.

        Returns:
            str: Foundation data with meta and provenance stripped, excluding
            the application_protocol.
        """
        return _compact_json(build_foundation_payload())

    @mcp.tool(
        name="humanizer_get_lexical_patterns",
        annotations={
            "title": "Get Lexical Patterns",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_lexical_patterns(params: RiskLevelInput) -> str:
        """Returns flagged words (verbs, adjectives, nouns, transitions, qualifiers,
        adverbs), substitution lists, vocabulary diversity rules, word-length
        patterns, nominalization rules, abstract/concrete balance, function-word
        patterns, and adverb patterns. Top-level meta.usage and
        meta.application_rule are surfaced as top-level fields.

        Args:
            params: RiskLevelInput with optional risk_level filter. When set,
                filters every severity-bearing array in the payload:
                flagged_verbs, flagged_adjectives, flagged_nouns,
                flagged_transitions, flagged_qualifiers.items, and
                adverb_patterns.flagged_ai_adverbs.

        Returns:
            str: Lexical patterns data, optionally filtered by risk level.
        """
        data = _strip_meta(load_json("lexical_patterns.json"))
        if params.risk_level:
            rl = params.risk_level.lower()
            if rl == "medium":
                rl = "moderate"

            def _matches(item: Any) -> bool:
                return isinstance(item, dict) and item.get("severity", "").lower() == rl

            # Flat top-level arrays of {ai_word|ai_phrase, severity, ...}
            for key in (
                "flagged_verbs",
                "flagged_adjectives",
                "flagged_nouns",
                "flagged_transitions",
            ):
                if isinstance(data.get(key), list):
                    data = {**data, key: [w for w in data[key] if _matches(w)]}

            # flagged_qualifiers nests its array under .items
            fq = data.get("flagged_qualifiers")
            if isinstance(fq, dict) and isinstance(fq.get("items"), list):
                data = {
                    **data,
                    "flagged_qualifiers": {
                        **fq,
                        "items": [w for w in fq["items"] if _matches(w)],
                    },
                }

            # adverb_patterns nests its array under .flagged_ai_adverbs
            ap = data.get("adverb_patterns")
            if isinstance(ap, dict) and isinstance(ap.get("flagged_ai_adverbs"), list):
                data = {
                    **data,
                    "adverb_patterns": {
                        **ap,
                        "flagged_ai_adverbs": [
                            w for w in ap["flagged_ai_adverbs"] if _matches(w)
                        ],
                    },
                }
        return _compact_json(data)

    @mcp.tool(
        name="humanizer_get_structural_patterns",
        annotations={
            "title": "Get Structural Patterns",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_structural_patterns() -> str:
        """Returns sentence length targets, syntactic variety rules, punctuation
        diversity guidance, and part-of-speech distribution targets.

        Returns:
            str: Structural patterns data with meta stripped.
        """
        data = _strip_meta(load_json("structural_patterns.json"))
        return _compact_json(data)

    @mcp.tool(
        name="humanizer_get_sentiment_tone",
        annotations={
            "title": "Get Sentiment & Tone Rules",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_sentiment_tone() -> str:
        """Returns neutral bias rules, emotional layering techniques, subjectivity
        guidance, and sensing/experience language patterns.

        Returns:
            str: Sentiment and tone data with meta stripped.
        """
        data = _strip_meta(load_json("sentiment_tone.json"))
        return _compact_json(data)

    @mcp.tool(
        name="humanizer_get_discourse_cohesion",
        annotations={
            "title": "Get Discourse Cohesion Rules",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_discourse_cohesion() -> str:
        """Returns transition rules, discourse markers, modal/epistemic markers,
        cohesive device guidance, and repetition pattern rules.

        Returns:
            str: Discourse cohesion data with meta stripped.
        """
        data = _strip_meta(load_json("discourse_cohesion.json"))
        return _compact_json(data)

    @mcp.tool(
        name="humanizer_get_psycholinguistic_texture",
        annotations={
            "title": "Get Psycholinguistic Texture",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_psycholinguistic_texture() -> str:
        """Returns cognitive load markers, self-monitoring traces, lexical retrieval
        signatures, and discourse planning traces.

        Returns:
            str: Psycholinguistic texture data with meta stripped.
        """
        data = _strip_meta(load_json("psycholinguistic_texture.json"))
        return _compact_json(data)

    @mcp.tool(
        name="humanizer_get_content_profile",
        annotations={
            "title": "Get Content Profile",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_content_profile(params: ContentProfileInput) -> str:
        """Returns per-content-type adjustments that modulate the base rules.
        Profiles define perplexity/burstiness targets and layer-specific aggressiveness.

        Args:
            params: ContentProfileInput with optional content_type.

        Returns:
            str: The matching profile, or all profiles if 'all' or omitted.
        """
        profiles = load_json("content_profiles.json").get("profiles", {})
        ct_input = params.content_type or "all"

        if ct_input == "all":
            result = profiles
        else:
            ct = _resolve_content_type(ct_input, profiles)
            if ct in profiles:
                result = profiles[ct]
            else:
                result = {
                    "_warning": (
                        f"Content type '{params.content_type}' not found. "
                        f"Available: {list(profiles.keys())}. Returning all."
                    ),
                    "profiles": profiles,
                }

        return _compact_json(result)

    @mcp.tool(
        name="humanizer_get_anti_patterns",
        annotations={
            "title": "Get Anti-Patterns",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_anti_patterns(params: CategoryFilterInput) -> str:
        """Returns before/after rewrite examples showing AI-typical text transformed
        into human-sounding alternatives, with explanations of what changed.

        Args:
            params: CategoryFilterInput with optional category filter.

        Returns:
            str: Array of anti-pattern examples, optionally filtered by category.
        """
        data = load_json("anti_patterns.json")
        examples = data.get("patterns", data.get("examples", data if isinstance(data, list) else []))

        if params.category:
            cat = params.category.lower()
            examples = [e for e in examples if e.get("category", "").lower() == cat]

        # Defensive: this tool bypasses _strip_meta because it returns a
        # bare list. Still run _drop_keys so any provenance fields added to
        # individual patterns in future (research_basis, notes) are stripped.
        examples = [_drop_keys(e) for e in examples]

        return _compact_json(examples)

    @mcp.tool(
        name="humanizer_get_caveats",
        annotations={
            "title": "Get Caveats & Ethical Boundaries",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_get_caveats() -> str:
        """Returns ESL sensitivity notes, detector brittleness warnings, model
        evolution caveats, and ethical considerations for responsible use.

        Returns:
            str: Caveats data with meta stripped.
        """
        data = _strip_meta(load_json("caveats.json"))
        return _compact_json(data)
