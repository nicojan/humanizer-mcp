"""Step 2 — decision grid. No API, no generation. Offline scorer over a
writer × condition × task output tree.

Layout it scores:  eval/outputs/<writer>/<condition>/<task_id>.txt
Conditions:        unaided, rules, rules_loop
Writers:           any subdirs present (e.g. primary, weak)

The §6.3 anti-circularity rule is enforced in *how results are read*, not just
documented:

  - unaided vs rules  → judge on L0 adherence (neither optimizes against the
    checker, so the comparison is fair).
  - rules vs rules_loop → judge on HUMAN-LIKENESS texture, NEVER on L0. The loop
    fixes whatever L0 flags, so it wins L0 by construction; the only honest
    question is whether it keeps the text human. L0 for rules_loop is shown ONLY
    to confirm the loop did drive prohibitions down, explicitly labelled as
    rigged, not as evidence.

Humanness read (corrected 2026-06-29 audit). The proxy direction matters: in the
Step-0 corpus the AI pile scores HIGHER on hapax than human (human mean ~0.756 vs
AI ~0.819), so "hapax rose" is a move toward the AI side, not toward human. The
grid therefore reports each condition's distance from the HUMAN MEAN (in human-SD
units, z) and whether the loop moved toward or away from it — see eval/reference.py.
Two further corrections: (1) hapax_ratio is length-sensitive and the loop shrinks
text 13-35%, so n_words is shown and a length-robust diversity proxy (mattr) is
read alongside; (2) sentence_length_stdev (burstiness) is dropped from the verdict
because Step-0 AUC was 0.516 — it does not separate human from AI here.

Run:  python3 -m eval.grid"""

from pathlib import Path
from statistics import mean

from eval.corpus.loader import load_pile
from eval.reference import AI_DIR, HUMAN_DIR, move_verdict, pile_reference, z_to_human
from eval.scorers.l0_checker import score_adherence
from eval.scorers.texture import texture_features

CONDITIONS = ["unaided", "rules", "rules_loop"]
# Verdict proxies: hapax_ratio (the Step-0 discriminator, AUC 0.82) and mattr
# (its length-robust cousin). sentence_length_stdev is displayed but NOT a
# verdict input (Step-0 AUC 0.516 — non-discriminating).
HUMANNESS_PROXIES = ["hapax_ratio", "mattr"]


def _discover_writers(base: Path) -> list[str]:
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())


def score_cell(items: list[dict]) -> dict:
    if not items:
        return {
            "n": 0,
            "l0_per_1k": 0.0,
            "n_words": 0.0,
            "sentence_length_stdev": 0.0,
            **{p: 0.0 for p in HUMANNESS_PROXIES},
        }
    l0 = mean(score_adherence(i["text"])["weighted_per_1k"] for i in items)
    feats = [texture_features(i["text"]) for i in items]
    row = {
        "n": len(items),
        "l0_per_1k": round(l0, 3),
        "n_words": round(mean(len(i["text"].split()) for i in items), 1),
    }
    for proxy in HUMANNESS_PROXIES:
        row[proxy] = round(mean(f[proxy] for f in feats), 3)
    # Displayed for completeness, NOT a verdict input (see HUMANNESS_PROXIES).
    row["sentence_length_stdev"] = round(
        mean(f["sentence_length_stdev"] for f in feats), 3
    )
    return row


def run_grid(base: str | Path = "eval/outputs", writers: list[str] | None = None) -> dict:
    base = Path(base)
    writers = writers or [w for w in _discover_writers(base) if w in ("primary", "weak")] or _discover_writers(base)
    grid: dict[str, dict] = {}
    for writer in writers:
        grid[writer] = {}
        for condition in CONDITIONS:
            grid[writer][condition] = score_cell(load_pile(base / writer / condition))
    return grid


def _delta(a: float, b: float) -> str:
    d = round(b - a, 3)
    return f"{d:+.3f}"


def format_grid(grid: dict, human_ref: dict, ai_ref: dict) -> str:
    lines: list[str] = []
    for writer, cells in grid.items():
        lines.append(f"\n### writer: {writer}")
        header = (
            f"{'condition':<12} {'n':>3} {'words':>7} {'l0/1k':>8} "
            f"{'hapax':>7} {'mattr':>7} {'sent_sd':>8}"
        )
        lines.append(header)
        lines.append("-" * len(header))
        for condition in CONDITIONS:
            c = cells[condition]
            lines.append(
                f"{condition:<12} {c['n']:>3} {c['n_words']:>7} {c['l0_per_1k']:>8} "
                f"{c['hapax_ratio']:>7} {c['mattr']:>7} {c['sentence_length_stdev']:>8}"
            )
        u, r, lp = cells["unaided"], cells["rules"], cells["rules_loop"]
        lines.append(
            "  Q1 reading helps adherence?  "
            f"L0 unaided→rules {_delta(u['l0_per_1k'], r['l0_per_1k'])} "
            "(negative = more compliant from reading; FAIR comparison)"
        )
        lines.append(
            "  Q2 loop carries adherence?   "
            f"L0 rules→loop {_delta(r['l0_per_1k'], lp['l0_per_1k'])} "
            "(rigged by construction — NOT evidence)."
        )
        lines.append(
            f"     length rules→loop: {r['n_words']}→{lp['n_words']} words "
            f"({_delta(r['n_words'], lp['n_words'])}). hapax/ttr rise as text shrinks, "
            "so trust length-robust mattr over hapax here."
        )
        for proxy in HUMANNESS_PROXIES:
            hf = human_ref.get(proxy)
            if not hf:
                continue
            af = ai_ref.get(proxy, {})
            zr, zl = z_to_human(r[proxy], hf), z_to_human(lp[proxy], hf)
            za = z_to_human(af["mean"], hf) if af else 0.0
            verdict = move_verdict(r[proxy], lp[proxy], hf)
            lines.append(
                f"     {proxy:<11} human mean {hf['mean']} (z=0), AI mean z={za:+.2f}  |  "
                f"rules z={zr:+.2f} → loop z={zl:+.2f}  ⇒ {verdict.upper()}"
            )
        lines.append(
            "     (verdict = did the loop move TOWARD the human mean or AWAY toward the "
            "AI side? 'away_from_human' is NOT a humanness improvement.)"
        )
        lines.append(
            "     sent_stdev (burstiness) is excluded from the verdict: Step-0 AUC 0.516, "
            "it does not separate human from AI in this corpus."
        )
    return "\n".join(lines)


def main() -> None:
    grid = run_grid()
    print("=== Step 2 decision grid (writer × condition, deterministic) ===")
    if all(c["n"] == 0 for cells in grid.values() for c in cells.values()):
        print(
            "No outputs found. Populate eval/outputs/<writer>/<condition>/<task>.txt "
            f"(conditions: {CONDITIONS}), then re-run."
        )
        return
    human_ref = pile_reference(HUMANNESS_PROXIES, HUMAN_DIR)
    ai_ref = pile_reference(HUMANNESS_PROXIES, AI_DIR)
    print(format_grid(grid, human_ref, ai_ref))
    print(
        "\nAnti-circularity (spec §6.3): unaided-vs-rules is read on L0; "
        "rules-vs-loop is read on humanness texture, never on L0. The texture read is "
        "distance to the HUMAN MEAN (corrected 2026-06-29 — see module docstring and "
        "eval/reference.py), not a raw proxy delta. n is tiny — direction only."
    )


if __name__ == "__main__":
    main()
