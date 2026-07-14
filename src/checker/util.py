"""Shared helpers for the checker package."""


def excerpt(text: str, start: int, end: int, radius: int = 40) -> str:
    """Return a single-line snippet of text around [start, end) with ellipses."""
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    snippet = text[a:b].replace("\n", " ").strip()
    return ("…" if a > 0 else "") + snippet + ("…" if b < len(text) else "")
