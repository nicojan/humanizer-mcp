"""Content-type aliases shared by the guide readers and the checker."""

CONTENT_TYPE_ALIASES: dict[str, str] = {
    "prose": "general_prose",
    "general_prose": "general_prose",
    "general": "general_prose",
    "tech": "technical",
    "technical": "technical",
    "academic": "academic",
    "marketing": "marketing",
    "creative": "creative",
    "case_study": "case_study",
    "case-study": "case_study",
    "case study": "case_study",
    "portfolio": "case_study",
    "product": "case_study",
    "resume": "resume",
    "résumé": "resume",
    "cv": "resume",
    "label": "label",
    "labels": "label",
    "notes": "label",
}


def canonical_content_type(ct: str | None) -> str | None:
    """The canonical name for ct, or None when ct is missing or unknown."""
    if ct is None:
        return None
    return CONTENT_TYPE_ALIASES.get(ct.strip().lower())
