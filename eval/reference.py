"""Human/AI reference bands for the Step-2 grid, computed from the Step-0 piles.

WHY THIS EXISTS (audit correction, 2026-06-29). The first version of the grid
read a raw rules->loop delta on hapax_ratio and treated "higher" as "more human".
That is backwards. In the calibration corpus the AI pile scores *higher* on
hapax than the human pile (human mean ~0.756 vs AI mean ~0.819; this is why the
Step-0 spike scores discrimination as max(auc, 1-auc) — the discriminating
direction is "AI is higher"). So raising hapax moves text away from the human
centre and toward the AI distribution. "Texture improved" was reading an
AI-ward move as a human-ward one.

The honest test is not "did the proxy rise" but "did the loop move the text
toward the human band or past it". This module builds both piles' bands and
classifies a rules->loop move against the human distribution. It does not score
L0 and is never used to separate human from AI (that is eval/spike.py); it only
re-orients the rules-vs-loop texture read.

No models, no API. Pure stdlib over the .txt piles."""

from pathlib import Path
from statistics import mean, pstdev

from eval.corpus.loader import load_pile
from eval.scorers.texture import texture_features

HUMAN_DIR = "eval/corpus/human"
AI_DIR = "eval/corpus/ai"


def pile_reference(features: list[str], directory: str | Path) -> dict:
    """Per-feature mean / sd / observed range for one pile. {} if pile empty."""
    items = load_pile(directory)
    if not items:
        return {}
    feats = [texture_features(i["text"]) for i in items]
    ref: dict[str, dict] = {}
    for name in features:
        vals = [f[name] for f in feats]
        ref[name] = {
            "mean": round(mean(vals), 4),
            "sd": round(pstdev(vals), 4) if len(vals) >= 2 else 0.0,
            "lo": round(min(vals), 4),
            "hi": round(max(vals), 4),
            "n": len(vals),
        }
    return ref


def z_to_human(value: float, human_feat: dict) -> float:
    """Signed distance from the human mean in human-SD units. 0 = human mean."""
    sd = human_feat.get("sd") or 0.0
    if sd == 0:
        return 0.0
    return round((value - human_feat["mean"]) / sd, 2)


def move_verdict(rules_val: float, loop_val: float, human_feat: dict) -> str:
    """Did the rules->loop move go toward the human mean or away from it?

    'away' is the failure case the original grid mislabelled as improvement.
    Distance is measured to the human MEAN (the centre we want to approach),
    not to the wide observed range (one outlier human can sit deep in AI
    territory, so the range alone is too permissive a target)."""
    if not human_feat:
        return "unknown"
    d_rules = abs(rules_val - human_feat["mean"])
    d_loop = abs(loop_val - human_feat["mean"])
    if round(d_loop - d_rules, 4) == 0:
        return "flat"
    return "toward_human" if d_loop < d_rules else "away_from_human"
