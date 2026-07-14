"""Step 1 — minimal harness. No API, no generation. Offline scorer.

You produce outputs under each condition (in Claude, your pipeline, or by hand,
from the prompts in eval/tasks.py) and save them as text files under
eval/outputs/<condition>/. The harness scores each pile on L0 (compliance) and the
deterministic texture features, and prints a comparison.

Step 1 has no repair loop, so comparing conditions on both L0 and texture is fair
(neither optimizes against the checker — spec §6.3). The rules+loop condition and
its anti-circularity split arrive in Step 2.

Run:  python -m eval.harness   (no API key required)"""

from pathlib import Path
from statistics import mean

from eval.corpus.loader import load_pile
from eval.scorers.l0_checker import score_adherence
from eval.scorers.texture import FEATURE_NAMES, texture_features

CONDITIONS = ["unaided", "rules"]
_HEADLINE_FEATURE = "sentence_length_stdev"


def score_condition(items: list[dict]) -> dict:
    if not items:
        row = {"n": 0, "mean_l0_per_1k": 0.0}
        row.update({f"mean_{name}": 0.0 for name in FEATURE_NAMES})
        return row
    l0 = [score_adherence(i["text"])["weighted_per_1k"] for i in items]
    feats = [texture_features(i["text"]) for i in items]
    row = {"n": len(items), "mean_l0_per_1k": round(mean(l0), 3)}
    for name in FEATURE_NAMES:
        row[f"mean_{name}"] = round(mean(f[name] for f in feats), 3)
    return row


def run_harness(outputs_dir: str | Path = "eval/outputs") -> list[dict]:
    base = Path(outputs_dir)
    rows: list[dict] = []
    for condition in CONDITIONS:
        items = load_pile(base / condition)
        rows.append({"condition": condition, **score_condition(items)})
    return rows


def format_table(rows: list[dict]) -> str:
    headline = f"mean_{_HEADLINE_FEATURE}"
    header = f"{'condition':<10} {'mean_l0_per_1k':>15} {headline:>27} {'n':>4}"
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row['condition']:<10} {row['mean_l0_per_1k']:>15} "
            f"{row.get(headline, 0.0):>27} {row['n']:>4}"
        )
    return "\n".join(lines)


def main() -> None:
    # Step 1 reads the primary writer's slice; the full writer × condition grid
    # (including rules_loop and the weak writer) is eval/grid.py.
    rows = run_harness("eval/outputs/primary")
    print("=== Step 1 minimal harness (unaided vs rules, deterministic) ===")
    if all(row["n"] == 0 for row in rows):
        print(
            "No outputs found. Populate eval/outputs/unaided/ and eval/outputs/rules/ "
            "with .txt files (one per task in eval/tasks.py), then re-run."
        )
        return
    print(format_table(rows))
    print(
        "\nReads off: does `rules` lower mean_l0_per_1k (more compliant) and/or raise "
        f"mean_{_HEADLINE_FEATURE} (burstier, the headline humanness proxy) vs "
        "`unaided`? Direction only — n is tiny. Full feature means are on each row."
    )


if __name__ == "__main__":
    main()
