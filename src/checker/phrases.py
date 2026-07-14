"""Fixed-phrase and flagged-term matching (case-insensitive, word-boundary)."""

import re

from src.checker.inflect import inflections


def find_phrases(text: str, phrases: list[str]) -> list[tuple[str, int]]:
    """Return (phrase, offset) for each word-boundary match of each phrase."""
    low = text.lower()
    out: list[tuple[str, int]] = []
    for p in phrases:
        pat = re.compile(r"\b" + re.escape(p.lower()) + r"\b")
        out.extend((p, m.start()) for m in pat.finditer(low))
    return out


def find_flagged_terms(text: str, terms: list[dict]) -> list[dict]:
    """terms: [{term, severity, alternatives}]. Word-boundary + inflection match.
    Multi-word terms are matched verbatim."""
    low = text.lower()
    results: list[dict] = []
    for entry in terms:
        term = entry["term"]
        forms = inflections(term)
        locations: list[int] = []
        for form in forms:
            pat = re.compile(r"\b" + re.escape(form) + r"\b")
            locations.extend(m.start() for m in pat.finditer(low))
        if locations:
            results.append(
                {
                    "type": "flagged_term",
                    "term": term,
                    "severity": entry.get("severity", ""),
                    "count": len(locations),
                    "locations": sorted(locations),
                    "alternatives": entry.get("alternatives", []),
                }
            )
    return results
