"""Punctuation correctness detection (AR-003).

Two finding categories:

- find_stacked_marks: adjacent internal-punctuation marks (',.' ';.' ',,'
  etc.). Treated as hard_violations because they are unambiguous mechanical
  errors. The pattern excludes period-led combinations ('.,', '.;', '.:')
  and ellipses to avoid false positives on legitimate abbreviations
  ('etc.,', 'e.g.,', 'i.e.,', 'Inc.,') and '...' sequences.

- find_unterminated: must_clear findings for (a) text whose final non-quote
  character is not a terminal mark, and (b) any span between terminal marks
  whose word count exceeds MAX_WORDS_PER_SENTENCE (likely a dropped period).
  Both flagged as must_clear so the LLM can justify legitimate titles or
  fragments rather than being veto-blocked.

- find_comma_splices: must_clear findings for two independent clauses joined by
  a bare comma. This is the classic artifact of AR-002 em-dash replacement (an
  em-dash pivot between independent clauses swapped for a comma). The heuristic
  is deliberately conservative — it fires only on 'comma + subject pronoun +
  finite verb' and explicitly skips legitimate complex sentences (a leading
  subordinator), parentheticals ('the plan, it seemed, would work'), compound
  sentences (', but we left'), and lists. Flagged as must_clear, never hard, so
  an intentional stylistic splice can be justified rather than veto-blocked.
"""

import re

from src.checker.util import excerpt

# Two adjacent internal-punctuation chars, OR an internal mark followed by
# a period (',.' ';.' ':.'), OR four-plus periods. Excludes '.,' '.;' '.:'
# (abbreviation-adjacent) and '...' (ellipsis).
_STACKED = re.compile(r"[,;:][,;:]|[,;:]\.|\.{4,}")

# A terminal sentence-end mark, optionally followed by closing quotes/parens.
_TERMINAL = re.compile(r"[.!?]+[\"')\]]*")

# Conservative threshold. Anything beyond this without a terminal mark is
# almost certainly a run-on or a dropped period.
MAX_WORDS_PER_SENTENCE = 45

# --- comma-splice detection constants ----------------------------------------

# Words that can begin an independent clause as its subject. Object/possessive
# pronouns (me, us, him, her, them) are excluded — they never start a clause.
_SUBJECT_PRONOUNS = frozenset(
    {"i", "we", "you", "he", "she", "it", "they"}
)

# A leading subordinator makes the comma legitimate (dependent clause first):
# "When it rains, it pours." / "If you build it, they will come."
_SUBORDINATORS = frozenset(
    {
        "when", "whenever", "while", "if", "unless", "until", "because",
        "although", "though", "since", "as", "after", "before", "whereas",
        "once", "provided", "wherever", "whether", "lest",
    }
)

# Auxiliary and copular verbs that, after a subject pronoun, mark a finite verb
# phrase and therefore an independent clause.
_AUX_BE = frozenset(
    {
        "is", "was", "are", "were", "am", "be", "been", "being",
        "will", "would", "can", "could", "shall", "should", "may", "might",
        "must", "do", "does", "did", "have", "has", "had", "get", "got", "gets",
    }
)

# Common base / irregular finite verbs not caught by the -ed / -s morphology
# rules below. Kept focused; recall is intentionally traded for precision since
# this is a must_clear (advisory) finding.
_COMMON_VERBS = frozenset(
    {
        "go", "went", "gone", "run", "ran", "see", "saw", "say", "said",
        "make", "made", "take", "took", "come", "came", "know", "knew",
        "think", "thought", "feel", "felt", "want", "need", "try", "use",
        "look", "find", "found", "give", "gave", "tell", "told", "keep",
        "kept", "put", "set", "let", "leave", "left", "build", "built",
        "ship", "send", "sent", "read", "write", "wrote", "hear", "heard",
        "show", "turn", "start", "stop", "help", "hold", "held", "bring",
        "brought", "mean", "meant", "win", "won", "lose", "lost", "become",
        "became", "begin", "began", "grow", "grew", "fall", "fell", "sit",
        "sat", "stand", "stood", "pay", "paid", "buy", "bought", "cut",
        "hit", "quit", "decide", "forget", "forgot",
    }
)

_WORD = re.compile(r"[A-Za-z']+")
_SENTENCE_BREAK = re.compile(r"[.!?]\s+")


def _is_finite_verb(word: str) -> bool:
    """Heuristic: does this token read as a finite verb? Conservative by design
    — used only after a confirmed subject pronoun, where the following word is
    almost always part of a verb phrase in well-formed English."""
    w = word.lower().strip("'")
    if not w or not w.isalpha():
        return False
    if w in _AUX_BE or w in _COMMON_VERBS:
        return True
    if len(w) > 3 and w.endswith("ed"):
        return True
    if len(w) > 3 and w.endswith("s") and not w.endswith(
        ("ss", "us", "is", "ous", "ics")
    ):
        return True
    return False


def _next_nonspace(text: str, idx: int) -> str:
    while idx < len(text) and text[idx] == " ":
        idx += 1
    return text[idx] if idx < len(text) else ""


def _span_has_finite_verb(span: str) -> bool:
    """Stricter verb test for deciding whether the text LEFT of a comma is an
    independent clause. Unlike _is_finite_verb it omits the bare -s rule:
    plural nouns ('keys', 'results') routinely appear in subject/intro phrases
    and would otherwise read as verbs. Requires an auxiliary/copula, a known
    base/irregular verb, or -ed morphology — enough to separate a real clause
    ('It was late') from a bare introductory element ('However', 'In 2020',
    'Yesterday')."""
    for w in _WORD.findall(span):
        wl = w.lower().strip("'")
        if wl in _AUX_BE or wl in _COMMON_VERBS:
            return True
        if len(wl) > 3 and wl.endswith("ed"):
            return True
    return False


def find_comma_splices(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r",", text):
        ci = m.start()
        toks = [
            (t.group(0), ci + 1 + t.start(), ci + 1 + t.end())
            for t in _WORD.finditer(text[ci + 1:])
        ]
        if not toks:
            continue
        first_w, _, _ = toks[0]
        if first_w.lower() not in _SUBJECT_PRONOUNS:
            continue

        # Verb candidate: the next token, allowing one optional -ly adverb
        # ("we quickly left").
        idx = 1
        if idx < len(toks) and toks[idx][0].lower().endswith("ly"):
            idx += 1
        if idx >= len(toks):
            continue
        verb_w, _, verb_end = toks[idx]
        if not _is_finite_verb(verb_w):
            continue

        # Parenthetical guard: "the plan, it seemed, would work" — the clause is
        # re-closed by a comma immediately after the verb.
        if _next_nonspace(text, verb_end) == ",":
            continue

        # Locate the start of the sentence the comma sits in.
        sent_start = 0
        for sb in _SENTENCE_BREAK.finditer(text[:ci]):
            sent_start = sb.end()
        left = text[sent_start:ci]

        # Subordinator guard: a dependent clause leading the sentence makes the
        # comma correct ("When it rains, it pours").
        lead = _WORD.search(left)
        lead_w = lead.group(0).lower() if lead else ""
        if lead_w in _SUBORDINATORS:
            continue

        # Non-finite intro guard: a sentence opening with an infinitive ("To be
        # fair, …") or a participial phrase ("Having finished …", "Frustrated
        # by …") is not an independent clause, even though it contains a verb
        # form. The leading 'to' / -ing / -ed marks the non-finite head.
        if lead_w == "to" or lead_w.endswith(("ing", "ed")):
            continue

        # Independent-clause guard: the left side must itself be a clause. This
        # rejects sentence-initial introductory elements ("However, it was…",
        # "In 2020, it…", "Yesterday, we…") whose left side has no finite verb.
        if not _span_has_finite_verb(left):
            continue

        out.append(
            {
                "rule": "AR-003",
                "type": "comma_splice",
                "offset": ci,
                "excerpt": excerpt(text, ci, ci + 1),
                "fix": (
                    "Two independent clauses are joined by only a comma. Use a "
                    "period (two sentences), a semicolon, or a colon; or add a "
                    "coordinating conjunction (and, but, so) after the comma. "
                    "If the splice is a deliberate stylistic choice, justify it."
                ),
            }
        )
    return out


def find_stacked_marks(text: str) -> list[dict]:
    out = []
    for m in _STACKED.finditer(text):
        out.append(
            {
                "rule": "AR-003",
                "type": "stacked_punctuation",
                "offset": m.start(),
                "excerpt": excerpt(text, m.start(), m.end()),
                "fix": (
                    "Remove the stray or duplicate mark. Keep only the "
                    "single correct internal or terminal punctuation."
                ),
            }
        )
    return out


def _span_between_terminals(text: str) -> list[tuple[int, int]]:
    """Return (start, end) byte spans for every region between terminal marks
    (or between text start/end and the nearest terminal mark)."""
    boundaries = [0]
    for m in _TERMINAL.finditer(text):
        boundaries.append(m.end())
    if boundaries[-1] != len(text):
        boundaries.append(len(text))
    spans = []
    for i in range(len(boundaries) - 1):
        a, b = boundaries[i], boundaries[i + 1]
        if b > a:
            spans.append((a, b))
    return spans


def find_unterminated(
    text: str, max_words: int = MAX_WORDS_PER_SENTENCE
) -> list[dict]:
    out = []
    stripped = text.strip()
    if not stripped:
        return out

    # (a) Final non-whitespace character must be a terminal mark, or a
    # terminal mark followed by closing quotes/parens.
    tail = stripped.rstrip("\"')]}")
    if tail and tail[-1] not in ".!?":
        # Locate the last terminal mark; flag everything after it.
        last_term_end = 0
        for m in _TERMINAL.finditer(text):
            last_term_end = m.end()
        start = last_term_end
        # If the tail-fragment is just a few words it may be a legitimate
        # title; flag at must_clear regardless so the LLM justifies.
        out.append(
            {
                "rule": "AR-003",
                "type": "missing_terminal_mark",
                "offset": start,
                "excerpt": excerpt(text, start, len(text)),
                "fix": (
                    "End with a terminal mark (period, question mark, or "
                    "exclamation point), or justify as an intentional "
                    "title/fragment."
                ),
            }
        )

    # (b) Any span between terminals longer than max_words is a run-on.
    seen = set()
    for start, end in _span_between_terminals(text):
        segment = text[start:end].strip()
        if not segment:
            continue
        wc = len(segment.split())
        if wc <= max_words:
            continue
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "rule": "AR-003",
                "type": "run_on_without_terminal",
                "offset": start,
                "excerpt": excerpt(text, start, min(end, start + 200)),
                "fix": (
                    f"This {wc}-word span has no internal terminal "
                    "punctuation. Break into shorter sentences with periods, "
                    "or use a semicolon to join two related independent "
                    "clauses."
                ),
            }
        )
    return out
