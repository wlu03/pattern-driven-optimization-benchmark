#!/usr/bin/env python3
"""finetune_transfer_summary.py — one-table summary of fine-tuning transfer to
the held-out (HO-*) patterns, across every (fine-tuned model x strategy x metric).

Reuses the validated held-out pairing + paired Wilcoxon signed-rank test from
scripts/finetune_transfer_eval.py (per-pattern delta = median-over-samples for
the fine-tuned model minus the base, tested non-parametrically). For each cell
it reports the held-out base rate, the fine-tuned rate, the delta, the Wilcoxon
two-sided p-value, and the direction.

Metrics: pass1 (correct & not unreliable), faithful (faithfulness_cell==FAITHFUL),
speedup (geomean speedup_vs_slow over correct rows).

Usage:
    python3 scripts/finetune_transfer_summary.py [--out results/transfer_eval/summary.txt]
"""
import argparse
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finetune_transfer_eval import (  # noqa: E402  reuse validated stats
    _read_held_out_rows, _wilcoxon_signed_rank, _median,
)

# (fine-tuned eval key, base scored-CSV key)
PAIRS = [
    ("r1-distill-qwen-1.5b-ft", "deepseek-r1-distill-qwen-1.5b"),
    ("r1-distill-qwen-7b-ft",   "deepseek-r1-distill-qwen-7b"),
    ("qwen2.5-coder-1.5b-ft",   "qwen2.5-coder-1.5b"),
]
STRATS = ["generic", "pattern-aware", "taxonomy-guided"]
METRICS = ["pass1", "faithful", "speedup"]
PARETO = Path("results/pareto")              # full base scored CSVs (filtered to HO- internally)
FT_HELDOUT = Path("results/pareto_ft_heldout")  # fine-tuned, held-out-only scored CSVs


def _overall(rows, metric):
    """Held-out overall: mean% for pass1/faithful, geomean for speedup."""
    vals = [v for d in rows.values() for v in d.values()
            if not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return float("nan")
    if metric == "speedup":
        ls = [math.log(v) for v in vals if v > 0]
        return math.exp(sum(ls) / len(ls)) if ls else float("nan")
    return sum(vals) / len(vals) * 100.0


def _paired_deltas(base, ft):
    """Per-pattern (median-over-samples) ft - base deltas, paired by pattern."""
    ds = []
    for pid in sorted(set(base) & set(ft)):
        b = _median(list(base[pid].values()))
        f = _median(list(ft[pid].values()))
        if math.isnan(b) or math.isnan(f):
            continue
        ds.append(f - b)
    return ds


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="results/transfer_eval/summary.txt")
    args = ap.parse_args()

    lines = []
    def emit(s=""):
        lines.append(s)

    emit("=" * 100)
    emit("FINE-TUNE TRANSFER TO HELD-OUT (HO-*)  —  base vs fine-tuned, paired Wilcoxon over patterns")
    emit("  pass1/faithful in %, speedup = geomean x ; delta = ft - base ; p = two-sided Wilcoxon ; n = paired patterns")
    emit("=" * 100)
    emit(f"{'fine-tuned model':24}{'strategy':16}{'metric':9}{'base':>9}{'finetuned':>11}"
         f"{'delta':>9}{'p':>9}  direction")
    emit("-" * 100)
    for ft, base in PAIRS:
        for strat in STRATS:
            bcsv = PARETO / f"{base}_{strat}_scored.csv"
            fcsv = FT_HELDOUT / f"{ft}_{strat}_scored.csv"
            if not bcsv.exists() or not fcsv.exists():
                emit(f"{ft:24}{strat:16}{'(missing CSV: ' + ('base' if not bcsv.exists() else 'ft') + ')'}")
                continue
            for metric in METRICS:
                br = _read_held_out_rows(bcsv, metric)
                fr = _read_held_out_rows(fcsv, metric)
                bo, fo = _overall(br, metric), _overall(fr, metric)
                w = _wilcoxon_signed_rank(_paired_deltas(br, fr))
                unit = "x" if metric == "speedup" else "%"
                delta = fo - bo
                star = "*" if (not math.isnan(w["p"]) and w["p"] < 0.05) else " "
                emit(f"{ft:24}{strat:16}{metric:9}{bo:>8.1f}{unit}{fo:>10.1f}{unit}"
                     f"{delta:>+8.1f}{unit}{w['p']:>8.3f}{star} {w['direction']} (n={w['n_effective']})")
        emit("-" * 100)

    report = "\n".join(lines)
    print(report)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(report + "\n")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
