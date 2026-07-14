"""Regex and heuristic detectors for banned sentence structures (Tier-1,
gate=checklist). Returns located candidates the LLM must rewrite or justify."""

import re

from src.checker.segment import split_sentences
from src.checker.util import excerpt

_NOMINAL = re.compile(r"\b\w+(?:tion|ment|ance|ence|ity|ness)\s+of\b", re.IGNORECASE)
_THIS_OPENER = re.compile(r"^(this|these|it)\b", re.IGNORECASE)

# A three-item coordinated list: "data, reporting, and alerts" /
# "approves, edits, or rejects" / "send, payment, or publish". The middle
# Oxford comma is optional.
_TRIAD = re.compile(
    r"\b[\w'\-]+,\s+[\w'\-]+,?\s+(?:and|or)\s+[\w'\-]+\b", re.IGNORECASE
)
# Max characters between two triad starts for them to count as "adjacent".
# A single triad is fine; clustered triads are the rule-of-three tell.
_TRIAD_WINDOW = 250


def find_regex_structures(text: str, structures: list[dict]) -> list[dict]:
    out: list[dict] = []
    for s in structures:
        det = s.get("detection", {})
        if det.get("method") != "regex":
            continue
        pat = re.compile(det["pattern"], re.IGNORECASE)
        for m in pat.finditer(text):
            out.append(
                {
                    "type": "banned_structure",
                    "id": s["id"],
                    "name": s["name"],
                    "confidence": det.get("confidence", "medium"),
                    "offset": m.start(),
                    "excerpt": excerpt(text, m.start(), m.end()),
                    "fix": s.get("fix", ""),
                }
            )
    return out


# PR2-#3: abstract-subject nouns that mark a copula-maxim closer.
_ABSTRACT_SUBJECTS = frozenset(
    {
        "craft", "work", "point", "truth", "reality", "design", "lesson",
        "difference", "answer", "rest", "order", "draft", "part", "thing",
        "idea", "goal", "key", "real",
    }
)
_COPULA = frozenset({"is", "was", "are", "were"})
_PARA = re.compile(r"\n\s*\n")
_MAXIM_OPENER = re.compile(r"^(?:the|my|our)\b", re.IGNORECASE)

# PR2-#6: a negated clause that may mirror a verb from the prior sentence.
_NEG_CLAUSE = re.compile(
    r"^(?:it|they|that)\s+"
    r"(?:never|does not|doesn't|do not|don't|will not|won't|cannot|can't)\s+"
    r"([a-z']+)",
    re.IGNORECASE,
)
_ALPHA = re.compile(r"[a-z']+", re.IGNORECASE)


def find_heuristic_structures(text: str) -> list[dict]:
    out: list[dict] = []
    out.extend(_stacked_nominalization(text))
    out.extend(_this_chain(text))
    out.extend(_copula_maxim_closer(text))
    out.extend(_verb_antithesis_pair(text))
    return out


def _copula_maxim_closer(text: str) -> list[dict]:
    """PR2-#3. A paragraph closing on a short abstract-subject copula maxim
    ('The craft is mostly restraint.'). Generalizes BS-014 beyond rarely/never
    aphorisms. Scoped tightly: paragraph-final, <=10 words, opens with
    The/My/Our, an abstract subject noun, a copula main verb, and no proper noun
    or number."""
    out: list[dict] = []
    cursor = 0
    for para in _PARA.split(text):
        start = text.find(para, cursor)
        cursor = start + len(para) if start >= 0 else cursor
        sents = split_sentences(para)
        if not sents:
            continue
        last = sents[-1].strip()
        words = last.split()
        if not 1 <= len(words) <= 10:
            continue
        if not _MAXIM_OPENER.match(last):
            continue
        toks = [w.strip(",.;:!?\"'()").lower() for w in words]
        copula_idx = next((i for i, t in enumerate(toks) if t in _COPULA), None)
        if copula_idx is None:
            continue
        if not set(toks[:copula_idx]) & _ABSTRACT_SUBJECTS:
            continue
        # No number, and no proper noun (a capitalized word after the opener).
        if any(any(c.isdigit() for c in w) for w in words):
            continue
        if any(w[:1].isupper() for w in words[1:]):
            continue
        s_start = max(text.find(last, max(start, 0)), 0)
        out.append(
            {
                "type": "banned_structure",
                "id": "BS-018",
                "name": "copula_maxim_closer",
                "confidence": "low",
                "offset": s_start,
                "excerpt": excerpt(text, s_start, s_start + len(last)),
                "fix": (
                    "End on the concrete thing, not a distilled lesson about it. "
                    "If the maxim is earned, attach it to a specific action "
                    "rather than floating it as a closer."
                ),
            }
        )
    return out


def _stem(word: str) -> str:
    w = word.lower()
    for suf, repl in (("ing", ""), ("ies", "y"), ("es", ""), ("ed", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)] + repl
    return w


def _verb_antithesis_pair(text: str) -> list[dict]:
    """PR2-#6. Two short sentences repeating a content verb with a polarity flip
    ('AI carries the busywork. It never carries the judgment.'). Verb-based
    relative of the copula antithesis BS-013. Fires only when the negated verb
    is actually repeated (by form or stem) from the prior sentence, which keeps
    ordinary narrative ('It never finished.') from matching."""
    sents = split_sentences(text)
    out: list[dict] = []
    if not sents:
        return out
    # Track a running search position so duplicate short sentences get distinct
    # offsets (find() without a start would always return the first occurrence).
    first = text.find(sents[0])
    cursor = first + len(sents[0]) if first >= 0 else 0
    for i in range(1, len(sents)):
        cur = sents[i].strip()
        cur_start = text.find(cur, cursor)
        if cur_start >= 0:
            cursor = cur_start + len(cur)
        m = _NEG_CLAUSE.match(cur)
        if not m:
            continue
        verb = m.group(1).lower()
        prev_words = {w.lower() for w in _ALPHA.findall(sents[i - 1])}
        stem = _stem(verb)
        # Exact-form repetition is the reliable signal; the stem fallback covers
        # minor inflection (carry/carries) but requires a >=3-char stem so short
        # function-word stems can't produce a spurious match.
        repeated = verb in prev_words or (
            len(stem) >= 3 and stem in {_stem(w) for w in prev_words}
        )
        if not repeated:
            continue
        s_start = max(cur_start, 0)
        out.append(
            {
                "type": "banned_structure",
                "id": "BS-020",
                "name": "verb_antithesis_pair",
                "confidence": "low",
                "offset": s_start,
                "excerpt": excerpt(text, s_start, s_start + len(cur)),
                "fix": (
                    "Make the positive claim once. If the boundary matters, "
                    "state it without mirroring the verb in the negative."
                ),
            }
        )
    return out


def find_rule_of_three_density(text: str) -> list[dict]:
    """Flag clusters of two or more parallel three-item lists close together.
    A lone triad is normal prose; adjacent triads are a strong AI tell
    (AP-011 / AP-020). Returns one located must_clear finding per cluster."""
    starts = [m.start() for m in _TRIAD.finditer(text)]
    if len(starts) < 2:
        return []

    out: list[dict] = []
    cluster = [starts[0]]

    def flush(group: list[int]) -> None:
        if len(group) < 2:
            return
        end = min(len(text), group[-1] + 40)
        out.append(
            {
                "type": "rule_of_three_density",
                "confidence": "low",
                "count": len(group),
                "offset": group[0],
                "excerpt": excerpt(text, group[0], end),
                "fix": (
                    "Two or more parallel three-item lists sit close together, a "
                    "strong rule-of-three tell. Vary one: drop to two items, "
                    "expand to four, or fold the items into a sentence with "
                    "commentary between them."
                ),
            }
        )

    for s in starts[1:]:
        if s - cluster[-1] <= _TRIAD_WINDOW:
            cluster.append(s)
        else:
            flush(cluster)
            cluster = [s]
    flush(cluster)
    return out


def _stacked_nominalization(text: str) -> list[dict]:
    out: list[dict] = []
    offset = 0
    for sent in split_sentences(text):
        start = text.find(sent, offset)
        offset = start + len(sent) if start >= 0 else offset
        if len(_NOMINAL.findall(sent)) >= 3:
            out.append(
                {
                    "type": "banned_structure",
                    "id": "BS-012",
                    "name": "stacked_nominalization",
                    "confidence": "medium",
                    "offset": max(start, 0),
                    "excerpt": excerpt(text, max(start, 0), max(start, 0) + len(sent)),
                    "fix": "Unpack the nouns back into verbs; name the agent.",
                }
            )
    return out


def _this_chain(text: str) -> list[dict]:
    sents = split_sentences(text)
    out: list[dict] = []
    run = 0
    run_start_idx = 0
    for i, sent in enumerate(sents):
        if _THIS_OPENER.match(sent.strip()):
            if run == 0:
                run_start_idx = i
            run += 1
        else:
            run = 0
        if run == 3:
            first = sents[run_start_idx]
            start = max(text.find(first), 0)
            out.append(
                {
                    "type": "banned_structure",
                    "id": "BS-009",
                    "name": "this_chain",
                    "confidence": "medium",
                    "offset": start,
                    "excerpt": excerpt(text, start, start + len(first)),
                    "fix": "Leave causal links implicit; vary sentence openings.",
                }
            )
    return out
