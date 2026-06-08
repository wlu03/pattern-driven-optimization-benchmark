#!/usr/bin/env python3
"""
cross_pattern_transfer.py
-------------------------
Cross-pattern transfer analysis: do per-category optimization skills co-vary
across models? Builds a model x category pass@1 matrix (15 models x 7 base
categories) and computes the Spearman rank-correlation between every pair of
categories across models.

High pairwise correlation => a model good at category A tends to be good at B
(the capability transfers / they share an underlying skill). Low correlation
=> the categories tap independent skills. Because all 15 models also differ in
raw capability, expect a positive baseline ("good models are good at most
things"); the interesting signal is which pairs deviate from that baseline.

Spearman is computed manually (average-rank + Pearson) so there is no scipy
dependency.

Usage:
    python3 scripts/cross_pattern_transfer.py [results/pareto_combined_scored.csv] \
        [--out results/cross_pattern_transfer.txt]
"""
import argparse
import csv
import re
import sys
from collections import defaultdict

BASE = ["AL", "CF", "DS", "HR", "IS", "MI", "SR"]


def _b(x):
    return str(x).strip().lower() in ("true", "1")


def _rankdata(vals):
    """Average ranks (1-based), ties share the mean of their rank span."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx = sum((a - mx) ** 2 for a in x) ** 0.5
    vy = sum((b - my) ** 2 for b in y) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


def _spearman(x, y):
    return _pearson(_rankdata(x), _rankdata(y))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results_csv", nargs="?",
                    default="results/pareto_combined_scored.csv")
    ap.add_argument("--out", default="results/cross_pattern_transfer.txt")
    args = ap.parse_args()
    csv.field_size_limit(sys.maxsize)

    mc = defaultdict(lambda: [0, 0])     # (model, cat) -> [correct, n]
    mtot = defaultdict(lambda: [0, 0])   # model -> [correct, n] (all base)
    models = set()
    with open(args.results_csv, newline="") as fh:
        for r in csv.DictReader(fh):
            pid = r.get("pattern_id", "")
            if pid.startswith(("HO-", "COMP")):
                continue
            c = re.split(r"[-_]", pid)[0]
            if c not in BASE:
                continue
            m = r.get("model", "")
            models.add(m)
            ok = _b(r.get("correct"))
            mc[(m, c)][1] += 1
            mc[(m, c)][0] += ok
            mtot[m][1] += 1
            mtot[m][0] += ok

    models = sorted(models)
    # column vectors: per category, the 15 model pass@1 values
    col = {c: [mc[(m, c)][0] / mc[(m, c)][1] * 100 for m in models] for c in BASE}
    overall = [mtot[m][0] / mtot[m][1] * 100 for m in models]

    lines = []
    def emit(s=""):
        lines.append(s)

    emit("=" * 60)
    emit(f"Cross-pattern transfer — Spearman across {len(models)} models")
    emit("=" * 60)

    # Spearman matrix.
    emit("\nSpearman rank-correlation between categories:")
    emit("      " + "".join(f"{c:>6}" for c in BASE))
    pairs = []
    for a in BASE:
        rowvals = []
        for b in BASE:
            rho = 1.0 if a == b else _spearman(col[a], col[b])
            rowvals.append(rho)
            if a < b:
                pairs.append((a, b, rho))
        emit(f"  {a:3} " + "".join(f"{v:>6.2f}" for v in rowvals))

    offdiag = [rho for _, _, rho in pairs]
    emit(f"\nmean off-diagonal Spearman: {sum(offdiag)/len(offdiag):+.2f}  "
         f"(baseline 'good models are good at most things')")

    pairs.sort(key=lambda x: -x[2])
    emit("\nmost-correlated category pairs (skills that co-vary):")
    for a, b, rho in pairs[:4]:
        emit(f"  {a}-{b}: {rho:+.2f}")
    emit("least-correlated / independent pairs:")
    for a, b, rho in pairs[-4:]:
        emit(f"  {a}-{b}: {rho:+.2f}")

    # Which category best predicts overall skill?
    emit("\ncategory vs overall pass@1 (best single predictor of model quality):")
    pred = sorted(BASE, key=lambda c: -_spearman(col[c], overall))
    for c in pred:
        emit(f"  {c}: {_spearman(col[c], overall):+.2f}")

    report = "\n".join(lines)
    print(report)
    with open(args.out, "w") as f:
        f.write(report + "\n")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
