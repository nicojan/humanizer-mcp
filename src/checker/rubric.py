"""The self-review rubric as the report serves it: short lines by default,
the full detail texts once on request, filtered by content type."""

from typing import Literal, get_args

from src.checker.loader import load_self_review
from src.content_types import canonical_content_type

RubricMode = Literal["short", "full"]

_FIELD_FOR_MODE: dict[str, str] = {"short": "short", "full": "detail"}
_ALL = "all"


def _applies(item: dict, canonical: str | None) -> bool:
    """A missing or unknown content type gets every item."""
    if canonical is None:
        return True
    return _ALL in item["applies_to"] or canonical in item["applies_to"]


def rubric_lines(content_type: str | None, mode: RubricMode = "short") -> list[str]:
    """The rubric lines for content_type: each applicable item's `short` line,
    or its `detail` when mode is "full". `history` is never returned."""
    if mode not in get_args(RubricMode):
        raise ValueError(f"rubric mode must be one of {get_args(RubricMode)}, got {mode!r}")
    field = _FIELD_FOR_MODE[mode]
    canonical = canonical_content_type(content_type)
    return [item[field] for item in load_self_review() if _applies(item, canonical)]
