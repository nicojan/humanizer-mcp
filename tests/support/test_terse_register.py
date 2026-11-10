"""The terse-register hard-negative set: a standing bar for every structural rule.

Round: 2026-11-09. Spec:
docs/superpowers/specs/2026-11-09-terse-register-negatives.md

Three rule rounds running, an adversarial review found false positives that
neither corpus tier could show, because both tiers are long-form prose and the
candidates targeted labels, captions, cells and slogans. This set is the
short functional writing those reviews kept inventing: dosing labels, menus,
listings, box scores, headlines, contract clauses, travel logistics, chat, UI
strings, captions, notes, signs and methods statements.

The bar: no regex structure fires on any line, and the full checker in label
mode reports nothing on any line but AR-003's missing full stop (which the
report already says to justify on titles and fragments). Each line is a whole
text in its register, so each is checked on its own.

A zero here is reportable because a discriminating control fires in the same
run: the numeral-contrast caption pattern rejected on 2026-11-09, which flags
ordinary dosing, scores and listings, has to keep firing on this set.
"""

import json
import re
from collections import Counter

import pytest

from src.checker import run_checks
from src.checker.loader import load_regex_structures
from src.checker.structures import find_regex_structures
from tests.support.fp_corpus import assert_terse_clear, terse_files, terse_lines

# The rejected BS-065 draft, kept as this set's control. It is NOT a rule.
_NUM_MANY = r"(?:two|three|four|five|six|seven|eight|nine|ten|twelve|twenty|\d+)"
_CONTROL = re.compile(
    r"(?m)(?:^[ \t]*|(?<=[.!?]\s))(?:one|a\s+single|" + _NUM_MANY + r")\s+[a-z][\w'’-]*,\s+"
    r"(?:one|a\s+single|all|every|each|no|zero|" + _NUM_MANY + r")\s+[\w'’-]+",
    re.IGNORECASE,
)

_REGEX_IDS = [s["id"] for s in load_regex_structures()]


def _rule(rule_id: str):
    rules = [s for s in load_regex_structures() if s["id"] == rule_id]
    return lambda text: find_regex_structures(text, rules)


def test_the_set_is_the_size_and_shape_it_claims():
    lines = terse_lines()
    registers = Counter(reg for reg, _ in lines)
    assert len(registers) >= 13, registers
    assert len(lines) >= 240, len(lines)
    assert all(n >= 15 for n in registers.values()), registers
    texts = [line for _, line in lines]
    assert len(texts) == len(set(texts)), [t for t, n in Counter(texts).items() if n > 1]
    # Em-dashes are a hard prohibition (AR-002) by policy, not a register
    # signal, so the set leaves them out rather than testing that policy here.
    assert not [t for t in texts if "—" in t]


def test_the_control_fires_so_the_zeros_below_mean_something():
    hits = [(reg, line) for reg, line in terse_lines() if _CONTROL.search(line)]
    assert len(hits) >= 10, hits
    assert len({reg for reg, _ in hits}) >= 3, hits


@pytest.mark.parametrize("rule_id", _REGEX_IDS)
def test_no_regex_structure_fires_on_any_line(rule_id):
    assert_terse_clear(_rule(rule_id), rule_id)


def test_the_full_checker_reports_only_missing_full_stops():
    """Label mode keeps burstiness and segment uniformity out of must_clear.
    Everything else runs. AR-003's missing terminal mark is expected on
    headlines and buttons and is excluded by type, not by rule."""
    unexpected = []
    for reg, line in terse_lines():
        report = run_checks(line, content_type="label")
        if report["hard_violations"]:
            unexpected.append((reg, line, report["hard_violations"]))
        for finding in report["must_clear"]:
            if finding.get("type") != "missing_terminal_mark":
                unexpected.append((reg, line, finding))
    assert not unexpected, unexpected[:5]


@pytest.mark.parametrize("path", terse_files(), ids=lambda p: p.stem)
def test_a_whole_register_read_as_one_document_trips_no_structure(path):
    """Run-length, budget and density rules only see a sequence. Read each
    register as a document of one-line paragraphs and check that none of them
    fires either."""
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    report = run_checks("\n\n".join(lines), content_type="label")
    assert not report["hard_violations"]
    # AR-003 is excluded here: headlines and buttons carry no full stop, so
    # twenty of them joined read as one long run-on. That is an artifact of the
    # joining; the per-line test above already covers AR-003's real behaviour.
    structural = [f for f in report["must_clear"] if f.get("rule") != "AR-003"]
    assert not structural, json.dumps(structural)[:600]
