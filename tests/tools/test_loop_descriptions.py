"""Every served description of the write-check-fix loop (server instructions,
the guide's verification instruction, the report's next_action, and the
foundation's enforcement.verification, primary_usage.statement and phase 9
stop_condition) must agree, so a model reads the final rubric="full" call and
the closing re-check before it ever sees a report."""

import re

from src.checker.report import _NEXT_ACTION
from src.server import SERVER_INSTRUCTIONS
from src.storage.json_store import load_json
from src.tools.read import build_guide_payload
from tests.checker.test_rubric import outside_quotes
from tests.data.test_guide_consistency import fires

_FULL = re.compile(r"""rubric=["']full["']""")
_RECHECK = re.compile(r"\bonce more\b[^.]*\bprohibitions_clear\b")
_TELLS = re.compile(r"—|,\s+not\b|\bnot just\b|\b(?:genuinely|honestly|actually|really|quietly)\b")


# The two-round cap applies to must_clear only; a hard violation is never justified.
_CAP = (
    "stop after two fix rounds and justify any must_clear item left. "
    "A hard_violation is never justified, so keep fixing until prohibitions_clear is true."
)


def _phase_9() -> dict:
    phases = load_json("foundation.json")["application_protocol"]["phases"]
    return next(p for p in phases if p["phase"] == 9)


def _loop_texts() -> dict[str, str]:
    foundation = load_json("foundation.json")
    return {
        "server": SERVER_INSTRUCTIONS,
        "guide": build_guide_payload("prose")["verification"]["instruction"],
        "report": _NEXT_ACTION,
        "enforcement.verification": foundation["enforcement"]["verification"],
        "primary_usage.statement": foundation["primary_usage"]["statement"],
        "phase_9.stop_condition": _phase_9()["stop_condition"],
    }


def test_every_loop_description_names_the_final_full_call():
    for name, text in _loop_texts().items():
        assert _FULL.search(text), name


def test_every_loop_description_ends_with_a_recheck_after_the_self_review():
    for name, text in _loop_texts().items():
        assert _RECHECK.search(text), name
        assert _RECHECK.search(text).start() > _FULL.search(text).start(), name


def test_five_loop_texts_carry_the_cap_sentence_before_the_final_call():
    for name, text in _loop_texts().items():
        if name == "phase_9.stop_condition":
            continue
        assert _CAP in text, name
        assert text.index("Re-run humanizer_check_text") < text.index(_CAP), name
        assert text.index(_CAP) < _FULL.search(text, text.index(_CAP)).start(), name


def test_phase_9_caps_must_clear_rounds_and_never_justifies_a_hard_violation():
    text = _phase_9()["stop_condition"]
    assert "A hard_violation is never justified" in text
    assert "must_clear" in text and "two fix rounds" in text


def test_no_loop_text_lets_a_hard_violation_be_justified():
    for name, text in _loop_texts().items():
        assert "justify anything left" not in text, name


def test_phase_9_tool_call_offers_the_rubric_parameter():
    params = _phase_9()["tools"][0]["params"]
    assert {"text", "content_type", "rubric"} <= set(params)
    assert "full" in params["rubric"] and "short" in params["rubric"]


def test_every_loop_description_limits_fixes_to_flagged_spans_and_two_rounds():
    for name, text in _loop_texts().items():
        assert "flagged span" in text and "two fix rounds" in text, name
        assert "assembled document" in text, name


def test_server_instructions_fit_the_client_cap():
    assert len(SERVER_INSTRUCTIONS) < 4096


def test_loop_descriptions_carry_no_tells():
    for name, text in _loop_texts().items():
        assert not _TELLS.search(text), name
        assert fires(outside_quotes(text)) == [], (name, fires(outside_quotes(text)))


def test_loop_tell_control():
    assert _TELLS.search("The loop is required, not optional polish.")
    assert not _FULL.search("then self-attest the manual_review items")
    assert not _RECHECK.search("re-run until prohibitions_clear is true")
