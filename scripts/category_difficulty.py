#!/usr/bin/env python3
"""
category_difficulty.py
----------------------
Per-category difficulty analysis over the combined scored sweep, testing the
two standing hypotheses:
  H1: IS (Input-Sensitive) is the hardest category.
  H2: AL (Algorithmic) and SR (Semantic-Redundancy) are the easiest.

Reports, for each of the 7 base categories (AL/CF/DS/HR/IS/MI/SR):
  - pass@1          (% of attempts that compile AND are correct)
  - compile rate
  - geomean_speedup (geometric mean of speedup_vs_slow over correct attempts)
  - faithful%       (FAITHFUL + FAITHFUL_ALTERNATIVE share)
plus per-pattern pass@1 spread within each category and a per-model robustness
check (how many models rank each category in their bottom-2 / top-2 by pass@1).

Usage:
    python3 scripts/category_difficulty.py [results/pareto_combined_scored.csv] \
        [--out results/category_difficulty.txt]
"""
import argparse
import csv
import math
import re
import sys
from collections import defaultdict

BASE = ["AL", "CF", "DS", "HR", "IS", "MI", "SR"]


def _b(x):
    return str(x).strip().lower() in ("true", "1")


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _cat(pid):
    if pid.startswith("HO-"):
        return "HO:" + pid.split("-")[1]
    if pid.startswith("COMP"):
        return "COMP"
    return re.split(r"[-_]", pid)[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results_csv", nargs="?",
                    default="results/pareto_combined_scored.csv")
    ap.add_argument("--out", default="results/category_difficulty.txt")
    args = ap.parse_args()
    csv.field_size_limit(sys.maxsize)

    cat = {c: {"n": 0, "correct": 0, "compiles": 0, "logsp": [], "faithful": 0}
           for c in BASE}
    patt = defaultdict(lambda: [0, 0])          # pid -> [correct, n]
    modelcat = defaultdict(lambda: [0, 0])      # (model, cat) -> [correct, n]

    with open(args.results_csv, newline="") as fh:
        for r in csv.DictReader(fh):
            pid = r.get("pattern_id", "")
            c = _cat(pid)
            if c not in cat:
                continue
            s = cat[c]
            s["n"] += 1
            if _b(r.get("compiles")):
                s["compiles"] += 1
            correct = _b(r.get("correct"))
            patt[pid][1] += 1
            patt[pid][0] += correct
            mk = (r.get("model", ""), c)
            modelcat[mk][1] += 1
            modelcat[mk][0] += correct
            if correct:
                s["correct"] += 1
                sp = _f(r.get("speedup_vs_slow"))
                if sp > 0:
                    s["logsp"].append(math.log(sp))
            if r.get("faithfulness_cell", "") in ("FAITHFUL", "FAITHFUL_ALTERNATIVE"):
                s["faithful"] += 1

    def pass1(c):
        return cat[c]["correct"] / cat[c]["n"] * 100 if cat[c]["n"] else 0.0

    lines = []
    def emit(s=""):
        lines.append(s)

    emit("=" * 64)
    emit("Per-category difficulty  (base 27-pattern categories)")
    emit("=" * 64)
    emit(f"{'cat':4}{'n':>7}{'pass@1':>9}{'compile':>9}{'geomean_sp':>12}{'faithful%':>11}")
    emit("-" * 64)
    for c in sorted(BASE, key=pass1):           # hardest (lowest pass@1) first
        s = cat[c]
        gm = math.exp(sum(s["logsp"]) / len(s["logsp"])) if s["logsp"] else 0.0
        emit(f"{c:4}{s['n']:>7}{pass1(c):>8.1f}%{s['compiles']/s['n']*100:>8.1f}%"
             f"{gm:>11.2f}x{s['faithful']/s['n']*100:>10.1f}%")

    # Per-pattern spread within each category.
    emit("\nPer-pattern pass@1 spread within each category:")
    catpat = defaultdict(list)
    for pid, (cor, n) in patt.items():
        catpat[_cat(pid)].append((pid, cor / n * 100))
    for c in BASE:
        ps = sorted(catpat[c], key=lambda x: x[1])
        if not ps:
            continue
        lo, hi = ps[0], ps[-1]
        emit(f"  {c}: {lo[1]:.0f}%..{hi[1]:.0f}%  "
             f"(worst {lo[0]} {lo[1]:.0f}%, best {hi[0]} {hi[1]:.0f}%)  [{len(ps)} patterns]")

    # Per-model robustness of the category ranking.
    models = sorted({m for m, _ in modelcat})
    bottom2 = defaultdict(int)
    top2 = defaultdict(int)
    for m in models:
        order = sorted(BASE, key=lambda c: (modelcat[(m, c)][0] /
                                            max(modelcat[(m, c)][1], 1)))
        for c in order[:2]:
            bottom2[c] += 1
        for c in order[-2:]:
            top2[c] += 1
    emit(f"\nPer-model robustness across {len(models)} models "
         f"(times a category is in a model's bottom-2 / top-2 by pass@1):")
    for c in sorted(BASE, key=lambda c: -bottom2[c]):
        emit(f"  {c}: bottom-2 x{bottom2[c]:<3} top-2 x{top2[c]}")

    # Hypothesis verdict.
    ranked = sorted(BASE, key=pass1)
    emit("\nHypothesis test:")
    emit(f"  hardest by pass@1 : {ranked[0]} ({pass1(ranked[0]):.1f}%)  "
         f"[H1 'IS hardest' -> IS is rank {ranked.index('IS')+1}/7, "
         f"bottom-2 for {bottom2['IS']}/{len(models)} models]")
    emit(f"  easiest by pass@1 : {ranked[-1]} ({pass1(ranked[-1]):.1f}%)  "
         f"[H2 'AL/SR easiest' -> AL rank {ranked.index('AL')+1}/7, "
         f"SR rank {ranked.index('SR')+1}/7]")
    gm = {c: (math.exp(sum(cat[c]['logsp']) / len(cat[c]['logsp']))
              if cat[c]['logsp'] else 0.0) for c in BASE}
    hardest_sp = min(BASE, key=lambda c: gm[c])
    emit(f"  hardest to speed up: {hardest_sp} ({gm[hardest_sp]:.2f}x geomean)")

    report = "\n".join(lines)
    print(report)
    with open(args.out, "w") as f:
        f.write(report + "\n")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
