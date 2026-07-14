from src.checker.report import assemble_report


def test_prohibitions_clear_true_when_no_hard():
    r = assemble_report([], [], {"sentence_count": 3})
    assert r["prohibitions_clear"] is True
    assert "manual_review" in r and r["manual_review"]
    assert "next_action" in r
    assert "note" in r


def test_prohibitions_clear_false_with_hard():
    r = assemble_report([{"rule": "AR-002", "type": "em_dash"}], [], {})
    assert r["prohibitions_clear"] is False
    assert r["hard_violations"]


def test_must_clear_passed_through():
    r = assemble_report([], [{"type": "flagged_term", "term": "delve"}], {})
    assert r["must_clear"][0]["term"] == "delve"
