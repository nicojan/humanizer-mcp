from eval.scorers.l0_checker import score_adherence, HARD_WEIGHT, MUST_WEIGHT


def test_clean_text_has_zero_hard_violations():
    result = score_adherence("The dog ran fast across the field. Birds sang nearby.")
    assert result["hard"] == 0
    assert result["weighted_per_1k"] >= 0.0
    assert result["word_count"] > 0


def test_em_dash_is_a_hard_violation():
    # AR-002: em-dashes are a hard prohibition the checker detects.
    result = score_adherence("Wait—stop right there.")
    assert result["hard"] >= 1
    assert result["weighted_per_1k"] > 0.0


def test_weighting_is_severity_scaled_and_per_1k():
    result = score_adherence("Wait—stop right now.")
    expected = HARD_WEIGHT * result["hard"] + MUST_WEIGHT * result["must"]
    assert result["weighted_per_1k"] == round(expected / result["word_count"] * 1000, 3)
    assert (HARD_WEIGHT, MUST_WEIGHT) == (3, 1)
