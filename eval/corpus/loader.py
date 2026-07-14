"""Loads plain-text calibration/benchmark piles from a directory of .txt files."""

from pathlib import Path


def load_pile(directory: str | Path) -> list[dict]:
    d = Path(directory)
    items: list[dict] = []
    for path in sorted(d.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        items.append({"name": path.stem, "text": text})
    return items
