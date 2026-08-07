"""Em-dash detection (AR-002). Flags U+2014 and the '--' digraph.
The en-dash (U+2013) is allowed for ranges and is not flagged."""

import re

from src.checker.util import excerpt

_EMDASH = re.compile(r"—|-{2,}")
# A line made only of hyphens, pipes, colons and spaces is markdown structure
# (a table separator '|---|---|', a setext underline, a '---' horizontal rule
# or front-matter fence), never an em-dash digraph. Checking the whole line
# keeps a genuine inline 'word--word' flagged while markdown chrome passes.
_STRUCTURAL_LINE = re.compile(r"^[\s\-|:]+$")


def _is_markdown_structure(text: str, offset: int) -> bool:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    line = text[start:] if end == -1 else text[start:end]
    return bool(_STRUCTURAL_LINE.match(line))


def find_emdashes(text: str) -> list[dict]:
    out = []
    for m in _EMDASH.finditer(text):
        if _is_markdown_structure(text, m.start()):
            continue
        out.append(
            {
                "rule": "AR-002",
                "type": "em_dash",
                "offset": m.start(),
                "excerpt": excerpt(text, m.start(), m.end()),
                "fix": (
                    "Replace with a semicolon, colon, or period (two "
                    "sentences); or parentheses for an aside. Use a comma only "
                    "when it does not join two independent clauses — a comma "
                    "between independent clauses is a comma splice (AR-003)."
                ),
            }
        )
    return out
