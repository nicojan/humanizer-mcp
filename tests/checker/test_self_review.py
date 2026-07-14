from src.checker import run_checks
from src.checker.loader import load_self_review


def test_load_self_review_returns_nonempty_list_of_strings():
    items = load_self_review()
    assert isinstance(items, list)
    assert len(items) >= 5
    assert all(isinstance(i, str) and i.strip() for i in items)


def test_self_review_preserves_abstraction_as_agent_line():
    joined = " ".join(load_self_review()).lower()
    assert "abstraction-as-agent" in joined or "abstract noun" in joined


def test_self_review_includes_performative_framing_beat():
    joined = " ".join(load_self_review()).lower()
    assert "performative framing beat" in joined
    # The definitional caveat must survive: device is legitimate in moderation.
    assert "moderation" in joined


def test_self_review_includes_human_likeness_dimensions():
    joined = " ".join(load_self_review()).lower()
    assert "rhythm" in joined
    assert "section" in joined  # section-to-section variation


def test_run_checks_manual_review_is_the_data_rubric():
    report = run_checks("The team shipped the update on a quiet Tuesday.", "prose")
    assert report["manual_review"] == load_self_review()


def test_next_action_sequences_self_review():
    report = run_checks("Anything at all.", "prose")
    assert "self" in report["next_action"].lower()
    assert "review" in report["next_action"].lower()
