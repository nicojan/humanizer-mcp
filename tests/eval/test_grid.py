from eval.grid import CONDITIONS, run_grid, score_cell


def test_score_cell_empty_is_safe():
    row = score_cell([])
    assert row["n"] == 0
    assert row["l0_per_1k"] == 0.0
    assert row["hapax_ratio"] == 0.0


def test_run_grid_scores_writer_condition_tree(tmp_path):
    base = tmp_path / "outputs"
    for condition in CONDITIONS:
        d = base / "primary" / condition
        d.mkdir(parents=True)
        (d / "t1.txt").write_text(
            "A short line here. Then a longer, winding clause that varies the "
            "rhythm and vocabulary across the whole little sample nicely.",
            encoding="utf-8",
        )

    grid = run_grid(base, writers=["primary"])

    assert set(grid["primary"]) == set(CONDITIONS)
    assert grid["primary"]["rules"]["n"] == 1
    assert 0.0 <= grid["primary"]["rules"]["hapax_ratio"] <= 1.0
