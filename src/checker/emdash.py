"""Em-dash detection (AR-002). Flags U+2014 and the '--' digraph.
The en-dash (U+2013) is allowed for ranges and is not flagged."""

import re

from src.checker.util import excerpt

_EMDASH = re.compile(r"—|--")


def find_emdashes(text: str) -> list[dict]:
    out = []
    for m in _EMDASH.finditer(text):
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
