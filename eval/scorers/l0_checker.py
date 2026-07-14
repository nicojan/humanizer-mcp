"""L0 adherence scorer: severity-weighted house-style compliance per 1k words.

NOT a humanness detector — the rules deliberately ban things humans do (em-dashes
above all), so human text trips L0 too. Use only to compare delivery conditions,
never to separate human from AI text (see eval/spike.py)."""

import os
from pathlib import Path

# eval is dev tooling run from the repo. The checker's loader reads
# HUMANIZER_DATA_DIR at call time (defaulting to the container path /app/data);
# point it at the repo's data/ if unset. Mirrors tests/conftest.py. setdefault
# respects an explicit override or pytest's conftest, and never affects the
# deployed server (eval is not imported there).
os.environ.setdefault(
    "HUMANIZER_DATA_DIR",
    str(Path(__file__).resolve().parents[2] / "data"),
)

from src.checker import run_checks  # noqa: E402  (env must be set before first data load)

HARD_WEIGHT = 3
MUST_WEIGHT = 1


def score_adherence(text: str, content_type: str | None = None) -> dict:
    report = run_checks(text, content_type)
    hard = len(report["hard_violations"])
    must = len(report["must_clear"])
    words = max(1, len(text.split()))
    weighted = HARD_WEIGHT * hard + MUST_WEIGHT * must
    return {
        "hard": hard,
        "must": must,
        "word_count": words,
        "weighted_per_1k": round(weighted / words * 1000, 3),
    }
