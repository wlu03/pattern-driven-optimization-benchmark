#!/usr/bin/env python3
"""finetune_transfer_eval.py — measure transfer of fine-tuning to held-out patterns.

The core experimental question: does fine-tuning a model on the 590-variant
training set transfer to the held-out patterns (post-cutoff, separate
authoring)? This compares a baseline run against a fine-tuned run on the
SAME held-out patterns, computes the paired per-pattern delta, and tests
significance via a Wilcoxon signed-rank test (the appropriate paired test
for non-parametric paired samples; see Georges et al. OOPSLA 2007).

Inputs:
  --base-csv PATH       results CSV from base model evaluated on held-out
  --finetuned-csv PATH  results CSV from fine-tuned model evaluated on held-out
  --metric METRIC       what to compare: pass1 | faithful | speedup | speedup_vs_ref
  --out DIR             output directory (default: transfer_eval/)

Both CSVs must contain rows for the same (pattern_id, sample_idx) pairs.
The script pairs them by (pattern_id, sample_idx) and computes per-pattern
delta. Aggregates per-category + overall.

Reports:
  * Per-category delta (mean + bootstrap 95% CI on the delta-of-medians)
  * Wilcoxon signed-rank test p-value for "did fine-tuning improve?"
  * Per-pattern detail table (which patterns benefited vs which regressed)
  * Single headline "transfer score" = signed area between the two CDFs
"""

import argparse
import csv
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────────────────────────
# Read + score
# ─────────────────────────────────────────────────────────────────────────────

def _row_score(row: dict, metric: str) -> float:
    """Numeric score per row for the chosen metric."""
    if metric == "pass1":
        correct = str(row.get("correct", "")).strip().lower() == "true"
        unreliable = str(row.get("unreliable", "")).strip().lower() == "true"
        return 1.0 if (correct and not unreliable) else 0.0
    if metric == "faithful":
        cell = str(row.get("faithfulness_cell", "")).strip().upper()
        return 1.0 if cell == "FAITHFUL" else 0.0
    if metric in ("speedup", "speedup_vs_slow"):
        try:
            v = float(row.get("speedup_vs_slow", 0) or 0)
            return v if v > 0 else float("nan")
        except (TypeError, ValueError):
            return float("nan")
    if metric == "speedup_vs_ref":
        try:
            v = float(row.get("speedup_vs_ref", 0) or 0)
            return v if v > 0 else float("nan")
        except (TypeError, ValueError):
            return float("nan")
    raise ValueError(f"unknown metric: {metric}")


def _category_short(s: str) -> str:
    if not isinstance(s, str):
        return ""
    parts = s.strip().split("-")
    for p in parts:
        if p in ("SR", "IS", "CF", "HR", "DS", "AL", "MI"):
            return p
        if p.startswith("HO") and len(parts) >= 2:
            for pp in parts:
                if pp in ("SR", "IS", "CF", "HR", "DS", "AL", "MI"):
                    return pp
    return ""


def _read_held_out_rows(path: Path, metric: str) -> dict:
    """Return {pattern_id: {sample_idx: score}} for held-out rows only."""
    rows = defaultdict(dict)
    if not path.exists():
        return rows
    with open(path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = r.get("pattern_id", "")
            if not pid.startswith("HO-"):
                continue  # held-out only
            sample = int(r.get("sample_idx", 0) or 0)
            score = _row_score(r, metric)
            rows[pid][sample] = score
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Statistics
# ─────────────────────────────────────────────────────────────────────────────

def _median(xs):
    s = sorted(x for x in xs if not (isinstance(x, float) and math.isnan(x)))
    n = len(s)
    if n == 0: return float("nan")
    return s[n // 2] if n % 2 == 1 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _bootstrap_ci(deltas, resamples=10_000, ci=95, seed=42):
    """Percentile-bootstrap CI on the median of deltas."""
    deltas = [d for d in deltas if not math.isnan(d)]
    if len(deltas) < 2:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    n = len(deltas)
    meds = []
    for _ in range(resamples):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        meds.append(_median(sample))
    meds.sort()
    alpha = (100 - ci) / 2.0
    lo_i = int(len(meds) * alpha / 100)
    hi_i = int(len(meds) * (100 - alpha) / 100) - 1
    return (_median(meds), meds[max(0, lo_i)], meds[min(len(meds) - 1, hi_i)])


def _wilcoxon_signed_rank(deltas):
    """Paired Wilcoxon signed-rank test. Returns dict with W_plus, W_minus,
    n_effective, p_two_sided, and direction ('improved' / 'regressed' / 'tie').

    For small n (≤20), exact distribution via enumeration. For large n,
    normal approximation. Stdlib-only.
    """
    d = [x for x in deltas if not (math.isnan(x) or x == 0)]
    n = len(d)
    if n < 2:
        return {"W_plus": float("nan"), "W_minus": float("nan"),
                "n_effective": n, "p": float("nan"), "direction": "insufficient"}
    abs_d = sorted([(abs(x), 1 if x > 0 else -1) for x in d])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs_d[j + 1][0] == abs_d[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    W_plus = sum(r for r, (_, s) in zip(ranks, abs_d) if s > 0)
    W_minus = sum(r for r, (_, s) in zip(ranks, abs_d) if s < 0)
    W = min(W_plus, W_minus)
    if n <= 20:
        from itertools import product
        count_le = 0
        total = 0
        for signs in product([1, -1], repeat=n):
            w_plus = sum(r for r, s in zip(ranks, signs) if s > 0)
            w_minus = sum(r for r, s in zip(ranks, signs) if s < 0)
            if min(w_plus, w_minus) <= W:
                count_le += 1
            total += 1
        p = count_le / total
    else:
        mu = n * (n + 1) / 4.0
        sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
        z = (W - mu) / sigma if sigma > 0 else 0.0
        p = math.erfc(abs(z) / math.sqrt(2))
    # Direction is determined by which sum dominates, NOT by W (which is min).
    if W_plus > W_minus:
        direction = "improved"   # positive deltas dominate
    elif W_plus < W_minus:
        direction = "regressed"
    else:
        direction = "tie"
    return {"W_plus": W_plus, "W_minus": W_minus, "n_effective": n,
            "p": p, "direction": direction}


# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-csv", required=True,
                        help="Results CSV from the BASE (un-tuned) model")
    parser.add_argument("--finetuned-csv", required=True,
                        help="Results CSV from the FINE-TUNED model")
    parser.add_argument("--metric", default="faithful",
                        choices=["pass1", "faithful", "speedup", "speedup_vs_ref"])
    parser.add_argument("--out", default="transfer_eval",
                        help="Output directory (default: transfer_eval/)")
    args = parser.parse_args()

    base_path = Path(args.base_csv)
    ft_path = Path(args.finetuned_csv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = _read_held_out_rows(base_path, args.metric)
    ft = _read_held_out_rows(ft_path, args.metric)
    common_pids = sorted(set(base.keys()) & set(ft.keys()))
    if not common_pids:
        print("No common held-out pattern_ids found between the two CSVs.")
        print(f"  base: {len(base)} pids, ft: {len(ft)} pids")
        return

    # Per-pattern paired score: take median over samples for each pattern in each CSV
    rows = []
    for pid in common_pids:
        base_s = list(base[pid].values())
        ft_s = list(ft[pid].values())
        if not base_s or not ft_s:
            continue
        b = _median(base_s)
        f = _median(ft_s)
        if math.isnan(b) or math.isnan(f):
            continue
        rows.append({
            "pattern_id": pid,
            "category":   _category_short(pid),
            "base":       b,
            "finetuned":  f,
            "delta":      f - b,
            "ratio":      (f / b) if (b != 0 and not math.isnan(b)) else float("nan"),
            "n_base":     len(base_s),
            "n_ft":       len(ft_s),
        })

    if not rows:
        print("No paired held-out patterns with usable scores in both CSVs.")
        return

    deltas = [r["delta"] for r in rows]
    med_delta, lo, hi = _bootstrap_ci(deltas)
    wcx = _wilcoxon_signed_rank(deltas)
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    n_pos = sum(1 for d in deltas if d > 0)
    n_neg = sum(1 for d in deltas if d < 0)
    n_zero = sum(1 for d in deltas if d == 0)

    print(f"Held-out transfer analysis ({args.metric})")
    print(f"  N paired held-out patterns:  {len(rows)}")
    print(f"  Base CSV:        {base_path}")
    print(f"  Fine-tuned CSV:  {ft_path}")
    print()
    print(f"Paired delta (finetuned - base):")
    print(f"  improved on    {n_pos}/{len(rows)} patterns")
    print(f"  regressed on   {n_neg}/{len(rows)} patterns")
    print(f"  unchanged on   {n_zero}/{len(rows)} patterns")
    print(f"  mean delta     = {mean_delta:+.4f}")
    print(f"  median delta   = {med_delta:+.4f}")
    print(f"  95% CI         = [{lo:+.4f}, {hi:+.4f}]")
    print()
    print(f"Wilcoxon signed-rank test (paired, two-sided):")
    print(f"  W+ = {wcx['W_plus']:.1f}  W- = {wcx['W_minus']:.1f}  "
          f"(n_effective = {wcx['n_effective']})")
    print(f"  p  = {wcx['p']:.4f}    direction = {wcx['direction']}")
    if wcx["p"] < 0.05 and wcx["direction"] in ("improved", "regressed"):
        print(f"  → Fine-tuning {wcx['direction']} held-out {args.metric} "
              f"(p < 0.05)")
    elif wcx["p"] < 0.05:
        print(f"  → Significant test but direction ambiguous (W+ == W-)")
    else:
        print(f"  → No significant transfer effect at α=0.05")
    print()

    # Per-category breakdown
    cat_rows = defaultdict(list)
    for r in rows:
        cat_rows[r["category"]].append(r)
    print(f"Per-category breakdown:")
    print(f"  {'cat':<6} {'n':>3} {'med_base':>10} {'med_ft':>10} "
          f"{'med_delta':>10} {'CI_lo':>10} {'CI_hi':>10}")
    for cat in sorted(cat_rows.keys()):
        crs = cat_rows[cat]
        cdeltas = [r["delta"] for r in crs]
        cmed, clo, chi = _bootstrap_ci(cdeltas)
        med_b = _median([r["base"] for r in crs])
        med_f = _median([r["finetuned"] for r in crs])
        print(f"  {cat:<6} {len(crs):>3} {med_b:>10.4f} {med_f:>10.4f} "
              f"{cmed:>+10.4f} {clo:>+10.4f} {chi:>+10.4f}")
    print()

    # Per-pattern detail
    print("Per-pattern (sorted by delta, descending = best fine-tune improvement):")
    print(f"  {'pattern':<10} {'cat':<4} {'base':>10} {'ft':>10} {'delta':>10}")
    for r in sorted(rows, key=lambda x: -x["delta"]):
        print(f"  {r['pattern_id']:<10} {r['category']:<4} "
              f"{r['base']:>10.4f} {r['finetuned']:>10.4f} {r['delta']:>+10.4f}")

    # CSV output
    out_csv = out_dir / "transfer_per_pattern.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pattern_id", "category", "base",
                                           "finetuned", "delta", "ratio",
                                           "n_base", "n_ft"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote per-pattern CSV: {out_csv}")


if __name__ == "__main__":
    main()
