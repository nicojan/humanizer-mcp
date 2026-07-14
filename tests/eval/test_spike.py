from eval.spike import MIN_AUC, run_spike


def test_min_auc_bar_is_preregistered():
    assert MIN_AUC == 0.75


def test_run_spike_passes_when_a_feature_separates(tmp_path):
    human_dir = tmp_path / "human"
    ai_dir = tmp_path / "ai"
    human_dir.mkdir()
    ai_dir.mkdir()
    # Human: bursty (a 1-word sentence next to a ~13-word one) -> high stdev.
    (human_dir / "h1.txt").write_text(
        "Go. We then wandered a very long and winding way around the entire lake.",
        encoding="utf-8",
    )
    (human_dir / "h2.txt").write_text(
        "Stop. I had never in my life seen anything quite so unexpectedly lovely before.",
        encoding="utf-8",
    )
    # AI: uniform short sentences -> near-zero stdev.
    (ai_dir / "a1.txt").write_text(
        "We walk here now. We walk there now. We walk back now.", encoding="utf-8"
    )
    (ai_dir / "a2.txt").write_text(
        "They run here fast. They run there fast. They run home fast.", encoding="utf-8"
    )

    verdict = run_spike(human_dir, ai_dir)

    assert verdict["passed"] is True
    assert verdict["best_discrimination"] >= 0.75
    assert verdict["best_feature"] in verdict["per_feature_discrimination"]
    assert verdict["n_human"] == 2 and verdict["n_ai"] == 2
    assert "human_mean_per_1k" in verdict["l0_note"]


def test_run_spike_fails_when_piles_are_identical(tmp_path):
    human_dir = tmp_path / "human"
    ai_dir = tmp_path / "ai"
    human_dir.mkdir()
    ai_dir.mkdir()
    same = "We walk here now. We walk there now. We walk back now."
    (human_dir / "h1.txt").write_text(same, encoding="utf-8")
    (human_dir / "h2.txt").write_text(same, encoding="utf-8")
    (ai_dir / "a1.txt").write_text(same, encoding="utf-8")
    (ai_dir / "a2.txt").write_text(same, encoding="utf-8")

    verdict = run_spike(human_dir, ai_dir)

    assert verdict["passed"] is False
    assert verdict["best_discrimination"] == 0.5
