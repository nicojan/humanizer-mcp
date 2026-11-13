from src.checker import run_checks
from src.checker.loader import load_self_review
from src.checker.rubric import rubric_lines


def _item(item_id: str) -> dict:
    return next(i for i in load_self_review() if i["id"] == item_id)


def test_load_self_review_returns_nonempty_list_of_items():
    items = load_self_review()
    assert isinstance(items, list)
    assert len(items) >= 5
    assert all(isinstance(i, dict) and i["short"].strip() and i["detail"].strip() for i in items)


def test_self_review_preserves_abstraction_as_agent_line():
    assert "abstract noun" in _item("abstraction_as_agent")["detail"].lower()


def test_self_review_includes_performative_framing_beat():
    detail = _item("performative_framing_beat")["detail"].lower()
    assert "performative framing beat" in detail
    # The definitional caveat must survive: device is legitimate in moderation.
    assert "moderation" in detail


def test_self_review_includes_human_likeness_dimensions():
    assert "cadence" in _item("rhythm")["detail"]
    assert "section" in _item("section_variation")["detail"].lower()


def test_run_checks_manual_review_is_the_data_rubric():
    report = run_checks("The team shipped the update on a quiet Tuesday.", "prose")
    assert report["manual_review"] == rubric_lines("prose", "short")


def test_next_action_sequences_self_review():
    report = run_checks("Anything at all.", "prose")
    assert "self" in report["next_action"].lower()
    assert "review" in report["next_action"].lower()
