"""Fixed-phrase and flagged-term matching (case-insensitive, word-boundary)."""

import re
from collections.abc import Sequence

from src.checker.inflect import inflections


def find_phrases(text: str, phrases: list[str]) -> list[tuple[str, int]]:
    """Return (phrase, offset) for each word-boundary match of each phrase."""
    low = text.lower()
    out: list[tuple[str, int]] = []
    for p in phrases:
        pat = re.compile(r"\b" + re.escape(p.lower()) + r"\b")
        out.extend((p, m.start()) for m in pat.finditer(low))
    return out


def _protected_spans(low: str, terms_of_art: Sequence[str]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for phrase in terms_of_art:
        pat = re.compile(r"\b" + r"\s+".join(re.escape(w) for w in phrase.split()) + r"\b")
        spans.extend((m.start(), m.end()) for m in pat.finditer(low))
    return spans


def find_flagged_terms(
    text: str, terms: list[dict], terms_of_art: Sequence[str] = ()
) -> list[dict]:
    """terms: [{term, severity, alternatives}]. Word-boundary + inflection match.
    Multi-word terms are matched verbatim. An occurrence that falls inside a
    term of art ("differentiated instruction") is not reported."""
    low = text.lower()
    protected = _protected_spans(low, terms_of_art)
    results: list[dict] = []
    for entry in terms:
        term = entry["term"]
        forms = inflections(term)
        locations: list[int] = []
        for form in forms:
            pat = re.compile(r"\b" + re.escape(form) + r"\b")
            locations.extend(
                m.start()
                for m in pat.finditer(low)
                if not any(s <= m.start() < e for s, e in protected)
            )
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
