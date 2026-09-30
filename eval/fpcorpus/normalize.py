"""Normalization for the Tier 2 long-form corpus.

Gutenberg plain text is hard-wrapped, so single newlines must become spaces
while blank lines stay paragraph breaks. Without that, split_sentences and
every paragraph-bounded detector both read the wrong thing.
"""

import re

_START = re.compile(r"^\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*$", re.M)
_END = re.compile(r"^\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*$", re.M)

# Smart punctuation to ASCII, matching the calibration corpus convention in
# eval/corpus/SOURCES.md. Em-dashes are deliberately NOT rewritten: the
# calibration corpus leaves them verbatim, and AR-002 is excluded from the
# structural sweep anyway.
_PUNCT = (
    ("‘", "'"),
    ("’", "'"),
    ("“", '"'),
    ("”", '"'),
    ("–", "-"),
    ("…", "..."),
)


def strip_gutenberg_chrome(raw: str) -> str:
    """Drop the licence header and footer, keeping only the work itself."""
    m = _START.search(raw)
    if m:
        raw = raw[m.end() :]
    m = _END.search(raw)
    if m:
        raw = raw[: m.start()]
    return raw


def unwrap(text: str) -> str:
    """Collapse hard wrapping. Blank lines survive as paragraph breaks."""
    paragraphs = []
    for para in re.split(r"\n[ \t]*\n+", text):
        para = re.sub(r"\s*\n\s*", " ", para).strip()
        if para:
            paragraphs.append(para)
    return "\n\n".join(paragraphs)


def normalize(raw: str) -> str:
    text = strip_gutenberg_chrome(raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for smart, plain in _PUNCT:
        text = text.replace(smart, plain)
    return unwrap(text)


__all__ = ["normalize", "strip_gutenberg_chrome", "unwrap"]
