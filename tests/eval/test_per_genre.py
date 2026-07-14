from eval.per_genre import GENRES, per_genre_discrimination


def test_per_genre_runs_on_synthetic_piles(tmp_path):
    human = tmp_path / "human"
    ai = tmp_path / "ai"
    human.mkdir()
    ai.mkdir()
    # Two genres, two samples each. Human texts are lexically varied; AI texts
    # repeat one word, so at least one feature must separate within each genre.
    (human / "human_prose_01.txt").write_text(
        "The garden brimmed with unfamiliar colour and quiet motion all morning.",
        encoding="utf-8",
    )
    (human / "human_prose_02.txt").write_text(
        "Rain arrived late, scattering loose petals across the warm stone path.",
        encoding="utf-8",
    )
    (ai / "ai_prose_01.txt").write_text(
        "The thing is the thing that the thing makes the thing do.",
        encoding="utf-8",
    )
    (ai / "ai_prose_02.txt").write_text(
        "The thing is the thing that the thing makes the thing go.",
        encoding="utf-8",
    )

    result = per_genre_discrimination(str(human), str(ai))

    assert "prose" in result
    assert result["prose"]["n_human"] == 2 and result["prose"]["n_ai"] == 2
    assert 0.0 <= result["prose"]["best_discrimination"] <= 1.0
    # genres with no samples are omitted, not errored
    assert set(result).issubset(set(GENRES))
