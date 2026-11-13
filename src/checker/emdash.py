"""Em-dash detection (AR-002). Flags U+2014 and the '--' digraph.
The en-dash (U+2013) is allowed for ranges and is not flagged. U+2014 fires
everywhere, inside code included, because a draft handed over in a fence is
still the deliverable. A hyphen run inside code (fenced blocks, inline backtick
spans) is code and is skipped. Outside code, a double hyphen that begins a
lowercase command-line flag ('--force') is skipped; '--Dana' and '--No, I
said.' are typed dashes and fire."""

import re
from bisect import bisect_right

from src.checker.util import excerpt

_EMDASH = re.compile(r"—|-{2,}")
# A line made only of hyphens, pipes, colons and spaces is markdown structure
# (a table separator '|---|---|', a setext underline, a '---' horizontal rule
# or front-matter fence), never an em-dash digraph. Checking the whole line
# keeps a genuine inline 'word--word' flagged while markdown chrome passes.
_STRUCTURAL_LINE = re.compile(r"^[\s\-|:]+$")
_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_BACKTICK_RUN = re.compile(r"`+")
_FLAG_PREFIX = " \t\r\n\f\v`("
# A quote before '--' is flag context only when the whole quoted thing is the
# flag: the token after the hyphens runs straight to the matching closing quote
# ('"--verbose"'). Otherwise '"--and when' is a typed em-dash.
_CLOSING_QUOTES = {
    '"': '"\u201d',
    "'": "'\u2019",
    "\u201c": "\u201d",
    "\u2018": "\u2019",
}
_FLAG_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")

_FIX = (
    "Replace it with a period (two sentences), or a semicolon when the two "
    "clauses are closely joined; use commas or parentheses for an aside. If "
    "the dash set up a reveal, put the point first. A comma between two "
    "independent clauses is a comma splice (AR-003)."
)


def _inline_spans(line: str, base: int) -> list[tuple[int, int]]:
    spans = []
    open_len = 0
    open_at = 0
    for m in _BACKTICK_RUN.finditer(line):
        n = m.end() - m.start()
        if open_len == 0:
            open_len, open_at = n, m.start()
        elif n == open_len:
            spans.append((base + open_at, base + m.end()))
            open_len = 0
    return spans


def _fence_opener(line: str) -> tuple[str, int] | None:
    """(char, length) when the line opens a fence. A backtick fence whose info
    string holds a backtick is not a fence (CommonMark); it is an inline span."""
    m = _FENCE_OPEN.match(line)
    if not m:
        return None
    run = m.group(1)
    if run[0] == "`" and "`" in line[m.end():]:
        return None
    return run[0], len(run)


def _closer_length(line: str, char: str) -> int:
    """Length of the fence run when the line is a possible closer for `char`
    (only that char, 0-3 spaces of indent, trailing spaces allowed), else 0."""
    stripped = line.strip(" ")
    indent = len(line) - len(line.lstrip(" "))
    if indent <= 3 and stripped and set(stripped) == {char}:
        return len(stripped)
    return 0


def _find_closer(lines: list[str], after: int, char: str, length: int) -> int:
    for j in range(after, len(lines)):
        if _closer_length(lines[j].rstrip("\r\n"), char) >= length:
            return j
    return -1


def _suffix_max_closers(lines: list[str]) -> dict[str, list[int]]:
    """For each fence char, out[c][i] is the longest possible closer on any
    line >= i. One backward pass; lets an opener skip a search that cannot
    succeed, which keeps the whole scan linear."""
    out = {c: [0] * (len(lines) + 1) for c in "`~"}
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].rstrip("\r\n")
        for c, arr in out.items():
            arr[i] = max(arr[i + 1], _closer_length(line, c))
    return out


def _code_spans(text: str) -> list[tuple[int, int]]:
    """Half-open (start, end) ranges of closed fenced blocks and same-line
    inline spans. A fence with no closing line hides nothing."""
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for raw in lines:
        offsets.append(offsets[-1] + len(raw))
    longest_after = _suffix_max_closers(lines)
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\r\n")
        opener = _fence_opener(line)
        closer = -1
        # Only search when a long enough closer exists below; the search then
        # succeeds and consumes the block, so no line is scanned twice.
        if opener and longest_after[opener[0]][i + 1] >= opener[1]:
            closer = _find_closer(lines, i + 1, *opener)
        if closer == -1:
            spans.extend(_inline_spans(line, offsets[i]))
            i += 1
        else:
            spans.append((offsets[i], offsets[closer + 1]))
            i = closer + 1
    return spans


def _is_cli_flag(text: str, start: int) -> bool:
    """'--' preceded by start/space/backtick/'(' (or a quote enclosing the whole
    flag) and followed by a lowercase ASCII letter."""
    after = start + 2
    if not (after < len(text) and "a" <= text[after] <= "z"):
        return False
    if start == 0 or text[start - 1] in _FLAG_PREFIX:
        return True
    closers = _CLOSING_QUOTES.get(text[start - 1])
    if closers is None:
        return False
    token = _FLAG_TOKEN.match(text, after)
    return bool(token) and token.end() < len(text) and text[token.end()] in closers


def _in_spans(starts: list[int], spans: list[tuple[int, int]], offset: int) -> bool:
    i = bisect_right(starts, offset) - 1
    return i >= 0 and offset < spans[i][1]


def _line_start(newlines: list[int], offset: int) -> int:
    i = bisect_right(newlines, offset - 1) - 1
    return newlines[i] + 1 if i >= 0 else 0


def find_emdashes(text: str) -> list[dict]:
    spans = _code_spans(text)
    starts = [s for s, _ in spans]
    structural: dict[int, bool] = {}
    newlines = [i for i, c in enumerate(text) if c == "\n"]
    out = []
    for m in _EMDASH.finditer(text):
        if m.group() != "\u2014" and _in_spans(starts, spans, m.start()):
            continue
        if m.end() - m.start() == 2 and m.group() == "--" and _is_cli_flag(text, m.start()):
            continue
        line_start = _line_start(newlines, m.start())
        if line_start not in structural:
            end = text.find("\n", m.start())
            line = text[line_start:] if end == -1 else text[line_start:end]
            structural[line_start] = bool(_STRUCTURAL_LINE.match(line))
        if structural[line_start]:
            continue
        out.append(
            {
                "rule": "AR-002",
                "type": "em_dash",
                "offset": m.start(),
                "excerpt": excerpt(text, m.start(), m.end()),
                "fix": _FIX,
            }
        )
    return out
