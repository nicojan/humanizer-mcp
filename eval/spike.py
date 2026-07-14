"""Step 0 — the signal spike (the gate). No API, no models — deterministic only.

Validates whether any single deterministic texture feature separates known-human
from known-AI text against a pre-registered bar. Discrimination is direction-
agnostic: a feature that perfectly anti-correlates is as useful as one that
correlates, so we score max(auc, 1 - auc). L0 (the checker) is NOT a discriminator
here — it measures house-style compliance, and human text trips it too — so it is
shown only as a sanity note.

If no cheap deterministic feature clears MIN_AUC on obvious cases, deterministic-
only measurement is too weak to grade subtle revisions: stop, and either accept a
heavier local-model signal, human-only rating, or keep the MCP as-is.

Run:  python -m eval.spike   (no API key required)"""

import sys
from statistics import mean

from eval.corpus.loader import load_pile
from eval.scorers.l0_checker import score_adherence
from eval.scorers.texture import FEATURE_NAMES, texture_features
from eval.separation import roc_auc

MIN_AUC = 0.75


def run_spike(human_dir, ai_dir) -> dict:
    human = load_pile(human_dir)
    ai = load_pile(ai_dir)
    human_feats = [texture_features(item["text"]) for item in human]
    ai_feats = [texture_features(item["text"]) for item in ai]

    per_feature: dict[str, float] = {}
    direction: dict[str, dict] = {}
    for name in FEATURE_NAMES:
        h_vals = [f[name] for f in human_feats]
        a_vals = [f[name] for f in ai_feats]
        auc = roc_auc(h_vals, a_vals)
        per_feature[name] = round(max(auc, 1 - auc), 3)
        h_mean, a_mean = mean(h_vals), mean(a_vals)
        # Which side is "more human"? max(auc, 1-auc) hides this, but it is the
        # whole point downstream: a humanizing edit that pushes a proxy toward
        # the AI mean is moving AWAY from human, not toward it (audit 2026-06-29).
        direction[name] = {
            "human_mean": round(h_mean, 4),
            "ai_mean": round(a_mean, 4),
            "more_human_when": "lower" if h_mean < a_mean else "higher",
        }

    best_feature = max(per_feature, key=per_feature.get)
    best_discrimination = per_feature[best_feature]

    return {
        "per_feature_discrimination": per_feature,
        "direction": direction,
        "best_feature": best_feature,
        "best_discrimination": best_discrimination,
        "min_auc": MIN_AUC,
        "passed": best_discrimination >= MIN_AUC,
        "n_human": len(human),
        "n_ai": len(ai),
        "l0_note": {
            "human_mean_per_1k": round(
                mean(score_adherence(i["text"])["weighted_per_1k"] for i in human), 3
            ),
            "ai_mean_per_1k": round(
                mean(score_adherence(i["text"])["weighted_per_1k"] for i in ai), 3
            ),
        },
    }


def main() -> None:
    verdict = run_spike("eval/corpus/human", "eval/corpus/ai")

    print("=== Step 0 signal spike (deterministic, no API) ===")
    print(f"n_human={verdict['n_human']}  n_ai={verdict['n_ai']}")
    print("Per-feature discrimination (max(auc, 1-auc)) + direction:")
    for name, score in sorted(
        verdict["per_feature_discrimination"].items(), key=lambda kv: -kv[1]
    ):
        d = verdict["direction"][name]
        print(
            f"  {name:<24} {score}   "
            f"human={d['human_mean']} ai={d['ai_mean']} "
            f"(more human when {d['more_human_when']})"
        )
    best_dir = verdict["direction"][verdict["best_feature"]]
    print(
        f"Best: {verdict['best_feature']} = {verdict['best_discrimination']} "
        f"(bar: {verdict['min_auc']}); on this feature human text is "
        f"{best_dir['more_human_when']} than AI — an edit that moves it the other "
        "way is moving toward AI, not toward human."
    )
    print(f"L0 sanity note (compliance, not separation): {verdict['l0_note']}")
    print(
        "VERDICT: "
        + (
            "PASS — a deterministic feature separates the piles"
            if verdict["passed"]
            else "FAIL — deterministic-only signal too weak; do not proceed"
        )
    )
    sys.exit(0 if verdict["passed"] else 1)


if __name__ == "__main__":
    main()
