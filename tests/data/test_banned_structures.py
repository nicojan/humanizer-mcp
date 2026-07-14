from src.storage.json_store import load_json


def test_banned_structures_loads():
    data = load_json("banned_structures.json")
    assert isinstance(data["structures"], list)
    assert len(data["structures"]) >= 5


def test_every_structure_has_required_fields():
    data = load_json("banned_structures.json")
    for s in data["structures"]:
        assert s["id"] and s["name"] and s["gate"] in ("hard", "checklist")
        assert s["detection"]["method"] in ("phrase", "regex", "heuristic")
        assert s["fix"]


def test_regex_structures_have_patterns():
    data = load_json("banned_structures.json")
    for s in data["structures"]:
        if s["detection"]["method"] == "regex":
            assert s["detection"]["pattern"]


def test_hard_gate_entries_are_phrase_method():
    data = load_json("banned_structures.json")
    for s in data["structures"]:
        if s["gate"] == "hard":
            assert s["detection"]["method"] == "phrase"
            assert isinstance(s["detection"]["phrases"], list)
