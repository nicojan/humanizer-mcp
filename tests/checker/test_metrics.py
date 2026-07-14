from src.checker.metrics import burstiness, target_stdev


def test_uniform_sentences_flagged():
    t = " ".join(["The system processes the incoming data quickly every time."] * 5)
    m = burstiness(t, 6.0)
    assert m["burstiness_flag"] is True
    assert m["sentence_count"] == 5


def test_varied_sentences_not_flagged():
    t = "Short. " + ("word " * 30).strip() + ". A medium sentence sits here now."
    m = burstiness(t, 2.0)
    assert m["burstiness_flag"] is False


def test_single_sentence_not_flagged():
    m = burstiness("Only one sentence here.", 6.0)
    assert m["burstiness_flag"] is False


def test_target_stdev_defaults_and_overrides():
    assert target_stdev(None) == 6.0
    assert target_stdev("technical") == 4.0
    assert target_stdev("unknown-type") == 6.0
