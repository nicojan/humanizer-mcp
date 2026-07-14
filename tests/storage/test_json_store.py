from src.storage.json_store import load_json


def test_load_foundation_from_repo_data():
    data = load_json("foundation.json")
    assert "absolute_rules" in data


def test_missing_file_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_json("does_not_exist.json")
