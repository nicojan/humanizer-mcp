"""Per-genre AUC diagnostic for the Step-0 calibration corpus. No API, no models.

This is NOT the gate — the pooled spike (`eval/spike.py`) is the pre-registered
go/no-go. This breaks per-feature discrimination down by genre so a single
highly-separable genre cannot mask a flat one (validity guard #6 in
docs/superpowers/specs/2026-06-29-humanizer-eval-corpus-construction.md).

Discrimination is direction-agnostic: max(auc, 1 - auc), same as the spike.

Run:  python3 -m eval.per_genre"""

from eval.corpus.loader import load_pile
from eval.scorers.texture import FEATURE_NAMES, texture_features
from eval.separation import roc_auc

GENRES = ["prose", "technical", "cover_letter", "marketing"]


def per_genre_discrimination(
    human_dir: str = "eval/corpus/human", ai_dir: str = "eval/corpus/ai"
) -> dict:
    human = load_pile(human_dir)
    ai = load_pile(ai_dir)
    out: dict[str, dict] = {}
    for genre in GENRES:
        h = [
            texture_features(i["text"])
            for i in human
            if i["name"].startswith(f"human_{genre}")
        ]
        a = [
            texture_features(i["text"])
            for i in ai
            if i["name"].startswith(f"ai_{genre}")
        ]
        if not h or not a:
            continue
        per_feature = {}
        for name in FEATURE_NAMES:
            auc = roc_auc([f[name] for f in h], [f[name] for f in a])
            per_feature[name] = round(max(auc, 1 - auc), 3)
        best = max(per_feature, key=per_feature.get)
        out[genre] = {
            "n_human": len(h),
            "n_ai": len(a),
            "best_feature": best,
            "best_discrimination": per_feature[best],
            "per_feature": per_feature,
        }
    return out


def main() -> None:
    result = per_genre_discrimination()
    print("=== Per-genre discrimination (diagnostic, NOT the gate) ===")
    for genre, r in result.items():
        print(
            f"\n[{genre}]  n_h={r['n_human']} n_a={r['n_ai']}  "
            f"best={r['best_feature']}={r['best_discrimination']}"
        )
        for name, value in sorted(r["per_feature"].items(), key=lambda kv: -kv[1]):
            print(f"    {name:<24} {value}")


if __name__ == "__main__":
    main()
