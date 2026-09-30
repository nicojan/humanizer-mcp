"""Assembles checker rule data from the JSON store. The only module in the
checker package that knows the on-disk data shapes; detectors stay pure."""

from src.storage.json_store import load_json


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


def load_self_review() -> list[str]:
    """The human-likeness self-review rubric the calling model runs against its
    own draft (the texture half of write→check→fix). Surfaced as the report's
    manual_review list. Lives in data so it can be edited and deployed by
    git-push + restart without a code change."""
    return load_json("self_review.json").get("self_review", {}).get("items", [])


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
