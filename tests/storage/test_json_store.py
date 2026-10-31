from src.storage.json_store import load_json


def test_load_foundation_from_repo_data():
    data = load_json("foundation.json")
    assert "absolute_rules" in data


def test_missing_file_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_json("does_not_exist.json")


def test_data_dir_env_var_wins(monkeypatch, tmp_path):
    from src.storage import json_store
    monkeypatch.setenv("HUMANIZER_DATA_DIR", str(tmp_path))
    assert json_store._data_dir() == tmp_path


def test_data_dir_uses_container_path_when_present(monkeypatch, tmp_path):
    from src.storage import json_store
    monkeypatch.delenv("HUMANIZER_DATA_DIR", raising=False)
    monkeypatch.setattr(json_store, "_CONTAINER_DATA_DIR", tmp_path)
    assert json_store._data_dir() == tmp_path


def test_data_dir_falls_back_to_repo_data_outside_container(monkeypatch, tmp_path):
    from pathlib import Path
    from src.storage import json_store
    monkeypatch.delenv("HUMANIZER_DATA_DIR", raising=False)
    monkeypatch.setattr(json_store, "_CONTAINER_DATA_DIR", tmp_path / "absent")
    repo_data = Path(__file__).resolve().parents[2] / "data"
    assert json_store._data_dir() == repo_data
    assert (json_store._data_dir() / "banned_structures.json").exists()
