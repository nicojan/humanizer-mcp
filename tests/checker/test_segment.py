from src.checker.segment import split_sentences


def test_split_basic():
    assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]


def test_split_empty():
    assert split_sentences("   ") == []


def test_split_single():
    assert split_sentences("Just one sentence with no end punctuation") == [
        "Just one sentence with no end punctuation"
    ]
