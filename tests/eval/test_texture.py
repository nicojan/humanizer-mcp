from eval.scorers.texture import FEATURE_NAMES, texture_features


def test_all_features_present_and_numeric():
    f = texture_features("Short. A much longer sentence with many more words here today.")
    for name in FEATURE_NAMES:
        assert name in f
        assert isinstance(f[name], (int, float))


def test_varied_lengths_have_higher_stdev_than_uniform():
    varied = texture_features(
        "Go. Then we walked a very long way around the whole lake together."
    )
    uniform = texture_features("We walked here. We walked there. We walked back.")
    assert varied["sentence_length_stdev"] > uniform["sentence_length_stdev"]


def test_type_token_ratio_bounds():
    assert texture_features("the the the the")["type_token_ratio"] < 0.5
    assert texture_features("alpha beta gamma delta")["type_token_ratio"] == 1.0


def test_bigram_repetition_higher_when_repeated():
    repeated = texture_features("we go we go we go we go")
    diverse = texture_features("alpha beta gamma delta epsilon zeta eta theta")
    assert repeated["bigram_repetition"] > diverse["bigram_repetition"]


def test_empty_text_is_safe():
    f = texture_features("")
    assert f["sentence_length_mean"] == 0.0
    assert f["type_token_ratio"] == 0.0
    assert f["mattr"] == 0.0


# A ~70-word varied passage (longer than the 50-token MATTR window).
_PASSAGE = (
    "The bridge washed out one spring and nobody replaced it for years. "
    "People drove the long way around, grumbled at potlucks, then quietly "
    "stopped grumbling. That is the strange arithmetic of inconvenience: give "
    "it enough seasons and a detour hardens into geography, into the ordinary "
    "shape of how a small town moves through its own valley without ever once "
    "remembering there had been a shorter road home before the flood came."
)


def test_mattr_is_length_robust_where_hapax_is_not():
    single = texture_features(_PASSAGE)
    doubled = texture_features(_PASSAGE + " " + _PASSAGE)
    # Duplicating the text makes almost every type recur, so hapax_ratio
    # collapses — it is strongly length-sensitive.
    assert doubled["hapax_ratio"] < single["hapax_ratio"] - 0.2
    # MATTR averages a sliding fixed-size window, so it barely moves.
    assert abs(doubled["mattr"] - single["mattr"]) < 0.05


def test_mattr_falls_back_to_ttr_below_window():
    # Four unique words, far below the window -> plain TTR == 1.0.
    assert texture_features("alpha beta gamma delta")["mattr"] == 1.0
