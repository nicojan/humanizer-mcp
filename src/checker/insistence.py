"""PR2-#1: credibility-insistence density detector.

A writer who repeatedly insists their own account is real/actual/genuine is
exhibiting a defensive credibility hedge. The DENSITY of the token set is the
signal, not any single use, so this is a must_clear density finding (never
hard). Token set and thresholds come from lexical_patterns.credibility_insistence
so the data file and the detector cannot drift.

Exclusions (must not count): the hyphenated/compound and fixed-phrase uses of
'real' (real-time, real estate, real number, real-world, in real terms), an
interrogative 'really?', one sentence-initial 'actually' (discourse marker), and
anything inside quotation marks.
"""

import re

from src.checker.util import excerpt

# Words, keeping hyphenated/apostrophe compounds intact: 'real-time' tokenizes as
# one token (so it never matches the bare 'real') while 'real' stays 'real'.
_WORD = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")

# Fixed phrases where 'real' is not a credibility assertion.
_REAL_PHRASES = re.compile(
    r"real[-\s]?time|real[-\s]?world|real\s+estate|real\s+number|in\s+real\s+terms",
    re.IGNORECASE,
)

# Sentence boundary: start of text, or after a terminal mark + space.
_SENT_START = re.compile(r"(?:^|[.!?]\s+)$")


def _spans(pattern: re.Pattern, text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in pattern.finditer(text)]


def _quoted_spans(text: str) -> list[tuple[int, int]]:
    return _spans(re.compile(r"\"[^\"]*\"|“[^”]*”"), text)


def _within(idx: int, spans: list[tuple[int, int]]) -> bool:
    return any(a <= idx < b for a, b in spans)


def find_credibility_insistence(text: str, config: dict) -> list[dict]:
    tokens = {t.lower() for t in config.get("tokens", [])}
    if not tokens:
        return []
    same_token_min = config.get("same_token_min", 3)
    rate_per_words = config.get("rate_per_words", 2 / 400)

    quoted = _quoted_spans(text)
    real_phrases = _spans(_REAL_PHRASES, text)

    counts: dict[str, int] = {}
    first_offset: dict[str, int] = {}
    actually_freebie_used = False

    for m in _WORD.finditer(text):
        w = m.group(0).lower()
        if w not in tokens:
            continue
        i = m.start()
        if _within(i, quoted):
            continue
        if w == "real" and _within(i, real_phrases):
            continue
        if w == "really":
            j = m.end()
            while j < len(text) and text[j] == " ":
                j += 1
            if j < len(text) and text[j] == "?":
                continue
        if w == "actually" and not actually_freebie_used and _SENT_START.search(
            text[:i]
        ):
            actually_freebie_used = True
            continue
        counts[w] = counts.get(w, 0) + 1
        first_offset.setdefault(w, i)

    total = sum(counts.values())
    if total == 0:
        return []
    word_count = len(text.split())
    dominant = max(counts, key=counts.get)
    over_same_token = counts[dominant] >= same_token_min
    over_rate = total >= same_token_min and word_count > 0 and (
        total / word_count > rate_per_words
    )
    if not (over_same_token or over_rate):
        return []

    off = first_offset[dominant]
    return [
        {
            "type": "credibility_insistence",
            "confidence": "low",
            "count": total,
            "dominant_token": dominant,
            "dominant_count": counts[dominant],
            "offset": off,
            "excerpt": excerpt(text, off, off + len(dominant)),
            "fix": (
                "You are repeatedly insisting the work is real/actual/genuine "
                f"('{dominant}' x{counts[dominant]}; {total} across the set). A "
                "human rarely needs to vouch that their own account is real. Cut "
                "the assertions and let the specifics carry the credibility; keep "
                "at most one if a contrast genuinely needs it."
            ),
        }
    ]
