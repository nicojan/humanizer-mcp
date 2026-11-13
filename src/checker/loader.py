"""Assembles checker rule data from the JSON store. The only module in the
checker package that knows the on-disk data shapes; detectors stay pure."""

import hashlib
import logging

from src.storage.json_store import load_json

logger = logging.getLogger(__name__)


def load_hard_phrases() -> list[str]:
    data = load_json("banned_structures.json")
    phrases: list[str] = []
    for s in data.get("structures", []):
        if s.get("gate") == "hard" and s["detection"].get("method") == "phrase":
            phrases.extend(s["detection"].get("phrases", []))
    return phrases


def load_regex_structures() -> list[dict]:
    data = load_json("banned_structures.json")
    return [
        s
        for s in data.get("structures", [])
        if s["detection"].get("method") == "regex"
    ]


def load_flagged_terms() -> list[dict]:
    """Flatten lexical_patterns flagged words/phrases into {term, severity,
    alternatives}. Pulls verbs/adjectives/nouns/transitions/qualifiers/adverbs
    and the common nominalizations. Excludes any term promoted to a Tier-1 hard
    phrase, so it is not double-reported in both hard_violations and must_clear."""
    lex = load_json("lexical_patterns.json")
    hard = {p.lower() for p in load_hard_phrases()}
    terms: list[dict] = []

    def add(items: list[dict], key: str) -> None:
        for it in items:
            word = it.get(key)
            if word:
                terms.append(
                    {
                        "term": word,
                        "severity": it.get("severity", ""),
                        "alternatives": it.get("alternatives", []),
                    }
                )

    add(lex.get("flagged_verbs", []), "ai_word")
    add(lex.get("flagged_adjectives", []), "ai_word")
    add(lex.get("flagged_nouns", []), "ai_word")
    add(lex.get("flagged_transitions", []), "ai_phrase")
    add(lex.get("flagged_qualifiers", {}).get("items", []), "ai_phrase")
    add(lex.get("adverb_patterns", {}).get("flagged_ai_adverbs", []), "ai_adverb")
    for nom in lex.get("nominalization", {}).get("common_nominalizations", []):
        if nom.get("nominal"):
            terms.append(
                {
                    "term": nom["nominal"],
                    "severity": "moderate",
                    "alternatives": [nom.get("verbal", "")],
                }
            )
    return [t for t in terms if t["term"].lower() not in hard]


def load_credibility_insistence() -> dict:
    """The credibility-insistence density config (token set + thresholds).
    Consumed by src.checker.insistence; kept in lexical_patterns so the data
    file and the detector cannot drift."""
    return load_json("lexical_patterns.json").get("credibility_insistence", {})


def load_terms_of_art() -> list[str]:
    """Lower-cased multi-word terms of art (lexical_patterns.terms_of_art.items).
    A flagged word inside one of these is a domain term with no plainer
    equivalent ("differentiated instruction"), so it is not reported. Data, so
    a new term deploys with a restart."""
    block = load_json("lexical_patterns.json").get("terms_of_art", {})
    return [str(it["phrase"]).lower() for it in block.get("items", []) if it.get("phrase")]


_RUBRIC_TEXT_FIELDS = ("id", "short", "detail")


def _raw_self_review_items() -> list:
    """The raw `self_review.items` list. Raises ValueError when the file's
    container is not an object holding an `items` list, so a broken container
    is never read as a string of characters or an empty rubric."""
    data = load_json("self_review.json")
    section = data.get("self_review") if isinstance(data, dict) else None
    items = section.get("items") if isinstance(section, dict) else None
    if not isinstance(items, list):
        raise ValueError("self_review.json needs a self_review object holding an items list")
    return items


def load_self_review_strict() -> list[dict]:
    """Every self-review item, validated. Raises ValueError on a legacy string
    or a malformed item. CI calls this so bad data fails the build; the runtime
    path (`load_self_review`) degrades instead."""
    return [_validated_rubric_item(i, n) for n, i in enumerate(_raw_self_review_items())]


def _legacy_item(text: str) -> dict:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return {"id": f"legacy_{digest}", "short": text, "detail": text, "applies_to": ["all"]}


def _lenient_item(item: object, index: int) -> dict | None:
    if isinstance(item, str) and item.strip():
        return _legacy_item(item.strip())
    try:
        return _validated_rubric_item(item, index)
    except ValueError as exc:
        logger.warning("skipping malformed self_review item: %s", exc)
        return None


def load_self_review() -> list[dict]:
    """The human-likeness self-review rubric the calling model runs against its
    own draft (the texture half of write→check→fix). Each item is an object with
    `id`, a one-line `short`, the full `detail`, `applies_to` (["all"] or
    canonical content types) and an optional `history` that is never served.
    Lives in data so it can be edited and deployed by git-push + restart
    without a code change. Degrades rather than failing a check: a legacy string
    item (an old volume under a new image) becomes an all-scoped object, and any
    other malformed item is skipped with a logged warning. Use
    `load_self_review_strict` where bad data must fail."""
    items = (_lenient_item(i, n) for n, i in enumerate(_raw_self_review_items()))
    return [i for i in items if i is not None]


def check_self_review_at_startup() -> int:
    """Validate the rubric once at server start and log the outcome (stderr via
    `logging`). Returns the number of items that will be served; never raises.
    A broken container is logged as an error and counts as zero items; legacy
    string items (an old data volume under a new image) are logged as a
    warning, since they are served but mean the data may be stale."""
    try:
        raw = _raw_self_review_items()
        served = load_self_review()
    except Exception as exc:  # noqa: BLE001  (startup must never fail on data)
        logger.error(
            "self_review: the rubric cannot be loaded (%s); "
            "check_text fails until the data is fixed",
            exc,
        )
        return 0
    legacy = sum(1 for i in raw if isinstance(i, str) and i.strip())
    if legacy:
        logger.warning(
            "self_review: %d legacy string items mapped to all-scoped objects; "
            "the data may be stale",
            legacy,
        )
    if len(served) == len(raw):
        logger.info("self_review: %d items loaded", len(served))
    else:
        logger.warning(
            "self_review: %d of %d items will be served; the rest are malformed",
            len(served),
            len(raw),
        )
    return len(served)


def _validated_rubric_item(item: object, index: int) -> dict:
    if not isinstance(item, dict):
        raise ValueError(f"self_review item {index} is not an object")
    for field in _RUBRIC_TEXT_FIELDS:
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise ValueError(f"self_review item {index} needs a non-empty {field!r}")
    applies = item.get("applies_to")
    if not isinstance(applies, list) or not applies or not all(isinstance(a, str) for a in applies):
        raise ValueError(f"self_review item {item['id']!r} needs a non-empty applies_to list")
    return dict(item)


def load_document_budgets() -> tuple[dict[str, int], dict[str, str]]:
    """(budget per rule id, name per rule id) for structures that carry a
    `document_budget`. A shape is budgeted when repetition is the tell and one
    instance is ordinary writing. See src/checker/budgets.py."""
    data = load_json("banned_structures.json")
    budgets: dict[str, int] = {}
    names: dict[str, str] = {}
    for s in data.get("structures", []):
        budget = s.get("document_budget")
        if budget:
            budgets[s["id"]] = int(budget)
            names[s["id"]] = s.get("name", s["id"])
    return budgets, names


def load_budget_only_ids() -> frozenset[str]:
    """Budgeted structures whose single instances are not reported. For a shape
    that is ordinary writing once and a tic only as a refrain ('I get my Fridays
    back'), an instance finding would be a false positive by construction; only
    the document_budget overrun is. See src/checker/budgets.py."""
    data = load_json("banned_structures.json")
    return frozenset(
        s["id"]
        for s in data.get("structures", [])
        if s.get("budget_only") and s.get("document_budget")
    )
