"""Light inflection expansion for single-word flagged terms.
Regular -s/-es/-ed/-ing/-d only. Not linguistically complete; multi-word
phrases are returned verbatim (matched as fixed strings elsewhere)."""


def inflections(word: str) -> set[str]:
    w = word.lower()
    if " " in w or not w.isalpha():
        return {w}
    forms = {w, w + "s", w + "es", w + "ed", w + "ing"}
    if w.endswith("e"):
        forms.add(w[:-1] + "ing")  # delve -> delving
        forms.add(w + "d")          # delve -> delved
    if w.endswith("y"):
        forms.add(w[:-1] + "ies")   # rely -> relies
        forms.add(w[:-1] + "ied")   # rely -> relied
    return forms
