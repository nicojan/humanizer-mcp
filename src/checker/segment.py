"""Naive sentence segmentation. Approximate by design (no NLP deps).

Known limitation: splits on abbreviations like 'Mr.'; acceptable for the
burstiness statistic, which only needs rough sentence lengths."""

import re

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [s for s in _SENT_SPLIT.split(text) if s.strip()]
