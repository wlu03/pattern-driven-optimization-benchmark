#!/usr/bin/env python3
"""sweep_select.py — rank the hyperparameter-sweep configs by how well they
recover held-out transfer vs the base model (and vs the phase-1 overfit recipe).

For each sweep subject, prints every config's held-out rate, the delta vs base,
and the paired Wilcoxon p — sorted best-first — reusing the validated held-out
pairing/stats from finetune_transfer_eval.py.

Usage:
    python3 scripts/sweep_select.py [--strategy pattern-aware] [--metric pass1]
"""
import argparse
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finetune_transfer_eval import _read_held_out_rows, _wilcoxon_signed_rank, _median

SUBJECTS = {  # short -> base scored-CSV key
    "qwen2.5-coder-1.5b": "qwen2.5-coder-1.5b",
    "r1-distill-qwen-7b": "deepseek-r1-distill-qwen-7b",
}
CONFIGS = ["baseline", "gentle", "gentle-lowrank", "medium", "lowlr", "replay", "gentle-replay"]
PARETO = Path("results/pareto")
FT = Path("results/pareto_ft_heldout")


def _overall(rows, metric):
    vals = [v for d in rows.values() for v in d.values()
            if not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return float("nan")
    if metric == "speedup":
        ls = [math.log(v) for v in vals if v > 0]
        return math.exp(sum(ls) / len(ls)) if ls else float("nan")
    return sum(vals) / len(vals) * 100.0


def _deltas(base, ft):
    ds = []
    for pid in sorted(set(base) & set(ft)):
        b = _median(list(base[pid].values()))
        f = _median(list(ft[pid].values()))
        if not (math.isnan(b) or math.isnan(f)):
            ds.append(f - b)
    return ds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="pattern-aware")
    ap.add_argument("--metric", default="pass1", choices=["pass1", "faithful", "speedup"])
    args = ap.parse_args()

    for short, base in SUBJECTS.items():
        bcsv = PARETO / f"{base}_{args.strategy}_scored.csv"
        if not bcsv.exists():
            print(f"\n{short}: base CSV missing ({bcsv})")
            continue
        br = _read_held_out_rows(bcsv, args.metric)
        base_rate = _overall(br, args.metric)
        print(f"\n=== {short}  (base held-out {args.metric} = {base_rate:.1f}%, "
              f"strategy={args.strategy}) ===")
        rows = []
        for cfg in ["(phase1)"] + CONFIGS:
            if cfg == "(phase1)":
                fcsv, label = FT / f"{short}-ft_{args.strategy}_scored.csv", "phase1-overfit"
            else:
                fcsv, label = FT / f"{short}-{cfg}-ft_{args.strategy}_scored.csv", cfg
            if not fcsv.exists():
                continue
            fr = _read_held_out_rows(fcsv, args.metric)
            rate = _overall(fr, args.metric)
            w = _wilcoxon_signed_rank(_deltas(br, fr))
            rows.append((label, rate, rate - base_rate, w["p"], w["direction"], w["n_effective"]))
        if not rows:
            print("  (no scored sweep CSVs yet)")
            continue
        rows.sort(key=lambda x: -x[1])  # best held-out rate first
        print(f"  {'config':18}{'held-out':>10}{'Δ vs base':>11}{'p':>9}  direction")
        for label, rate, d, p, dirn, n in rows:
            star = "*" if (not math.isnan(p) and p < 0.05) else " "
            print(f"  {label:18}{rate:>9.1f}%{d:>+10.1f}%{p:>8.3f}{star} {dirn} (n={n})")


if __name__ == "__main__":
    main()
