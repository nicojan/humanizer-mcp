from eval.harness import CONDITIONS, format_table, run_harness, score_condition
from eval.tasks import TASKS


def test_tasks_have_required_shape():
    assert len(TASKS) >= 3
    for task in TASKS:
        assert {"id", "genre", "prompt"} <= set(task)


def test_score_condition_empty_is_safe():
    row = score_condition([])
    assert row["n"] == 0
    assert row["mean_l0_per_1k"] == 0.0
    assert row["mean_sentence_length_stdev"] == 0.0


def test_run_harness_scores_each_condition(tmp_path):
    out = tmp_path / "outputs"
    (out / "unaided").mkdir(parents=True)
    (out / "rules").mkdir(parents=True)
    # unaided: uniform short sentences -> low burstiness.
    (out / "unaided" / "t1.txt").write_text(
        "We walk here now. We walk there now. We walk back now.", encoding="utf-8"
    )
    # rules: bursty -> higher burstiness.
    (out / "rules" / "t1.txt").write_text(
        "Go. We then wandered a very long and winding way around the lake.",
        encoding="utf-8",
    )

    rows = run_harness(out)

    assert [r["condition"] for r in rows] == CONDITIONS
    rules = next(r for r in rows if r["condition"] == "rules")
    unaided = next(r for r in rows if r["condition"] == "unaided")
    assert rules["mean_sentence_length_stdev"] > unaided["mean_sentence_length_stdev"]
    assert rules["n"] == 1


def test_format_table_includes_conditions_and_columns():
    rows = run_harness("eval/outputs")  # may be empty seed dirs; still formats
    table = format_table(rows)
    assert "condition" in table
    assert "mean_l0_per_1k" in table
