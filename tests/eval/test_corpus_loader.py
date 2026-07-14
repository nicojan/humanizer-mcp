from pathlib import Path

import pytest

from eval.corpus.loader import load_pile

_HUMAN_DIR = Path(__file__).resolve().parents[2] / "eval" / "corpus" / "human"
_CORPUS_PRESENT = _HUMAN_DIR.exists() and any(_HUMAN_DIR.glob("*.txt"))
_needs_corpus = pytest.mark.skipif(
    not _CORPUS_PRESENT,
    reason="human calibration corpus is not redistributed (copyrighted excerpts); "
    "see eval/corpus/SOURCES.md to reconstruct it from the archived source URLs",
)


def test_load_pile_reads_txt_sorted(tmp_path):
    (tmp_path / "b.txt").write_text("second text", encoding="utf-8")
    (tmp_path / "a.txt").write_text("  first text  ", encoding="utf-8")
    (tmp_path / "ignore.md").write_text("not loaded", encoding="utf-8")

    pile = load_pile(tmp_path)

    assert [item["name"] for item in pile] == ["a", "b"]
    assert pile[0]["text"] == "first text"  # stripped
    assert all(item["text"] for item in pile)


def test_load_pile_skips_empty_files(tmp_path):
    (tmp_path / "real.txt").write_text("content", encoding="utf-8")
    (tmp_path / "blank.txt").write_text("   \n  ", encoding="utf-8")

    pile = load_pile(tmp_path)

    assert [item["name"] for item in pile] == ["real"]


GENRES = ["prose", "technical", "cover_letter", "marketing"]


@_needs_corpus
def test_calibration_corpus_meets_spec():
    """The Step-0 corpus must clear the spec's ≥15-per-pile bar and stay
    genre-balanced (≥4 human samples per genre, paired by an AI pile that is
    at least as large — the AI pile may grow with other-model additions)."""
    repo_root = Path(__file__).resolve().parents[2]
    human = load_pile(repo_root / "eval" / "corpus" / "human")
    ai = load_pile(repo_root / "eval" / "corpus" / "ai")

    assert len(human) >= 15, "human pile below the spec's >=15 bar"
    assert len(ai) >= 15, "ai pile below the spec's >=15 bar"
    assert len(ai) >= len(human), "ai pile must pair (at least) every human sample"

    for genre in GENRES:
        human_in_genre = [i for i in human if i["name"].startswith(f"human_{genre}")]
        ai_in_genre = [i for i in ai if i["name"].startswith(f"ai_{genre}")]
        assert len(human_in_genre) >= 4, f"{genre}: human pile not balanced (>=4)"
        assert len(ai_in_genre) >= 4, f"{genre}: ai pile not balanced (>=4)"
