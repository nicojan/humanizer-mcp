"""Separation metric for the Step-0 spike. Pure Python — no numpy/sklearn.

AUC here = P(random human text scores higher than random AI text), the
Mann-Whitney U statistic normalized to [0, 1]. 1.0 = perfectly separated,
0.5 = indistinguishable."""

from statistics import mean


def roc_auc(human_scores: list[float], ai_scores: list[float]) -> float:
    if not human_scores or not ai_scores:
        raise ValueError("both score lists must be non-empty")
    wins = 0.0
    for h in human_scores:
        for a in ai_scores:
            if h > a:
                wins += 1.0
            elif h == a:
                wins += 0.5
    return wins / (len(human_scores) * len(ai_scores))


def separation_verdict(
    human_scores: list[float],
    ai_scores: list[float],
    min_auc: float = 0.75,
) -> dict:
    auc = roc_auc(human_scores, ai_scores)
    return {
        "auc": round(auc, 3),
        "min_auc": min_auc,
        "passed": auc >= min_auc,
        "human_mean": round(mean(human_scores), 3),
        "ai_mean": round(mean(ai_scores), 3),
        "n_human": len(human_scores),
        "n_ai": len(ai_scores),
    }
