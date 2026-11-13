import json

import pytest
from pydantic import ValidationError

from src.tools.check import CheckTextInput, check_text_handler


def test_handler_returns_compact_json():
    out = check_text_handler("The plan — bold.", None)
    assert '"prohibitions_clear":false' in out  # compact: no space after colon
    data = json.loads(out)
    assert data["hard_violations"]


def test_handler_clean_text_clear():
    out = check_text_handler(
        "We shipped on Tuesday. The team was tired but glad.", "prose"
    )
    data = json.loads(out)
    assert data["prohibitions_clear"] is True


def test_input_rejects_empty():
    with pytest.raises(ValidationError):
        CheckTextInput(text="")


def test_input_strips_and_accepts_content_type():
    m = CheckTextInput(text="  hello  ", content_type="tech")
    assert m.text == "hello"
    assert m.content_type == "tech"


def test_input_accepts_the_full_rubric():
    assert CheckTextInput(text="x", rubric="full").rubric == "full"
    assert CheckTextInput(text="x").rubric == "short"


def test_input_rejects_an_unknown_rubric_mode():
    with pytest.raises(ValidationError):
        CheckTextInput(text="x", rubric="long")


def test_handler_passes_the_rubric_mode_through():
    short = json.loads(check_text_handler("We shipped on Tuesday.", "prose"))
    full = json.loads(check_text_handler("We shipped on Tuesday.", "prose", "full"))
    assert len(short["manual_review"]) == len(full["manual_review"])
    assert sum(map(len, full["manual_review"])) > sum(map(len, short["manual_review"]))
