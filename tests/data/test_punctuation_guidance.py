"""AR-002 must steer em-dash replacement away from the comma-splice failure
mode, and AR-003 must name the comma splice as a checked error. These tests
pin the guidance wording so the rule text and the mechanical checker stay in
agreement."""

from src.storage.json_store import load_json


def _rule(foundation: dict, rule_id: str) -> dict:
    return next(
        r for r in foundation["absolute_rules"]["rules"] if r["id"] == rule_id
    )


def test_ar002_warns_against_comma_splice_substitution():
    f = load_json("foundation.json")
    directive = _rule(f, "AR-002")["directive"].lower()
    assert "comma splice" in directive


def test_ar003_names_comma_splice():
    f = load_json("foundation.json")
    directive = _rule(f, "AR-003")["directive"].lower()
    assert "comma splice" in directive
