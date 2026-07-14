"""Deterministic text-texture features — no models, no API.

Pure stdlib plus the checker's sentence splitter, so sentences are measured the
same way the deployed server measures them. These are the candidate human-vs-AI
discriminators the Step-0 spike evaluates; none is trusted in isolation."""

import re
import statistics
from collections import Counter

from src.checker.segment import split_sentences

_WORD = re.compile(r"[A-Za-z']+")

# Moving-average type-token ratio window. MATTR averages TTR over a sliding
# fixed-size window, which makes it length-invariant where raw type_token_ratio
# and hapax_ratio are not (both drift up as a text gets shorter). The Step-2
# loop shrinks outputs 13-35%, so the length-sensitive proxies confound the
# rules-vs-loop comparison; mattr is the length-robust diversity proxy.
# (Covington & McFall 2010, "Cutting the Gordian Knot: MATTR".)
_MATTR_WINDOW = 50

FEATURE_NAMES = [
    "sentence_length_stdev",
    "sentence_length_mean",
    "sentence_length_range",
    "type_token_ratio",
    "hapax_ratio",
    "mattr",
    "mean_word_length",
    "bigram_repetition",
]


def _words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def _mattr(words: list[str], window: int = _MATTR_WINDOW) -> float:
    """Moving-average type-token ratio. Length-invariant lexical diversity.

    For texts shorter than the window, falls back to plain TTR (no window to
    slide), which is the most we can say without inventing tokens."""
    n = len(words)
    if n == 0:
        return 0.0
    if n <= window:
        return len(set(words)) / n
    ratios = [
        len(set(words[i : i + window])) / window
        for i in range(n - window + 1)
    ]
    return sum(ratios) / len(ratios)


def texture_features(text: str) -> dict:
    sentences = split_sentences(text)
    lengths = [len(s.split()) for s in sentences]
    words = _words(text)
    n = len(words)
    counts = Counter(words)
    bigrams = list(zip(words, words[1:]))

    return {
        "sentence_length_stdev": (
            round(statistics.pstdev(lengths), 3) if len(lengths) >= 2 else 0.0
        ),
        "sentence_length_mean": round(statistics.mean(lengths), 3) if lengths else 0.0,
        "sentence_length_range": (max(lengths) - min(lengths)) if lengths else 0,
        "type_token_ratio": round(len(counts) / n, 4) if n else 0.0,
        "hapax_ratio": (
            round(sum(1 for c in counts.values() if c == 1) / len(counts), 4)
            if counts
            else 0.0
        ),
        "mattr": round(_mattr(words), 4),
        "mean_word_length": (
            round(sum(len(w) for w in words) / n, 3) if n else 0.0
        ),
        "bigram_repetition": (
            round(1 - len(set(bigrams)) / len(bigrams), 4) if bigrams else 0.0
        ),
    }
