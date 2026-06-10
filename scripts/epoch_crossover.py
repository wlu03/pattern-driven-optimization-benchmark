#!/usr/bin/env python3
"""epoch_crossover.py — map the in-distribution-transfer vs OOD-forgetting
tradeoff across fine-tuning epochs.

For each epoch-sweep variant (<short>-indist-ep<N>-ft) it compares, vs the base
model, on TWO held-outs:
  * in-distribution  : the held-out base-pattern variants (fine_tune/heldout_indist_variants.txt)
  * OOD              : the post-cutoff contamination held-out (pattern_id starts HO-)
paired by variant_id, paired Wilcoxon. The expected signature (Kumar et al. 2022)
is in-dist pass@1 rising with epochs while OOD pass@1 falls.

Base rows come from results/pareto/<base>_<strat>_scored.csv (full sweep);
fine-tuned rows from results/pareto_ft_indist/<variant>_<strat>_scored.csv.

Usage:
    python3 scripts/epoch_crossover.py [--strategy pattern-aware] [--metric pass1]
"""
import argparse
import csv
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finetune_transfer_eval import _row_score, _wilcoxon_signed_rank  # noqa: E402

csv.field_size_limit(sys.maxsize)

MODELS = {  # short -> base scored-CSV key
    "qwen2.5-coder-1.5b": "qwen2.5-coder-1.5b",
    "r1-distill-qwen-7b": "deepseek-r1-distill-qwen-7b",
}
EPOCHS = [1, 3, 6, 10]
PARETO = Path("results/pareto")
FT = Path("results/pareto_ft_indist")
INDIST_IDS = set(Path("fine_tune/heldout_indist_variants.txt").read_text().split())


def _read(path, metric, indist):
    """{variant_id: score} for either the in-dist held-out ids or the OOD (HO-) rows."""
    out = {}
    if not Path(path).exists():
        return out
    for r in csv.DictReader(open(path, newline="")):
        vid, pid = r.get("variant_id", ""), r.get("pattern_id", "")
        keep = (vid in INDIST_IDS) if indist else pid.startswith("HO-")
        if keep:
            out[vid] = _row_score(r, metric)
    return out


def _rate(d, metric):
    vals = [v for v in d.values() if not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return float("nan")
    if metric == "speedup":
        ls = [math.log(v) for v in vals if v > 0]
        return math.exp(sum(ls) / len(ls)) if ls else float("nan")
    return sum(vals) / len(vals) * 100.0


def _cmp(base, ft, metric):
    ds = []
    for vid in sorted(set(base) & set(ft)):
        b, f = base[vid], ft[vid]
        if not (math.isnan(b) or math.isnan(f)):
            ds.append(f - b)
    return _wilcoxon_signed_rank(ds), len(ds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="pattern-aware")
    ap.add_argument("--metric", default="pass1", choices=["pass1", "faithful", "speedup"])
    a = ap.parse_args()
    print(f"strategy={a.strategy}  metric={a.metric}  in-dist held-out variants={len(INDIST_IDS)}")

    for short, base in MODELS.items():
        bcsv = PARETO / f"{base}_{a.strategy}_scored.csv"
        if not bcsv.exists():
            print(f"\n{short}: base CSV missing"); continue
        b_in = _read(bcsv, a.metric, indist=True)
        b_ood = _read(bcsv, a.metric, indist=False)
        bi, bo = _rate(b_in, a.metric), _rate(b_ood, a.metric)
        print(f"\n=== {short}  (base: in-dist={bi:.1f}%  OOD={bo:.1f}%) ===")
        print(f"  {'epochs':>7}{'in-dist':>9}{'Δ':>7}{'p':>8}  | {'OOD':>7}{'Δ':>7}{'p':>8}")
        for e in EPOCHS:
            fcsv = FT / f"{short}-indist-ep{e}-ft_{a.strategy}_scored.csv"
            if not fcsv.exists():
                print(f"  {e:>7}   (not scored yet)"); continue
            # Guard against a still-in-progress / prematurely-scored cell: a
            # complete cell is 79 in-dist + 178 OOD = 257 rows. A partial would
            # otherwise pollute the table with tiny-denominator garbage.
            with open(fcsv, newline="") as _fh:
                _nrows = sum(1 for _ in csv.reader(_fh)) - 1
            if _nrows < 250:
                print(f"  {e:>7}   (incomplete: {_nrows} rows)"); continue
            f_in, f_ood = _read(fcsv, a.metric, True), _read(fcsv, a.metric, False)
            ri, ro = _rate(f_in, a.metric), _rate(f_ood, a.metric)
            (wi, ni), (wo, no) = _cmp(b_in, f_in, a.metric), _cmp(b_ood, f_ood, a.metric)
            si = "*" if (not math.isnan(wi["p"]) and wi["p"] < 0.05) else " "
            so = "*" if (not math.isnan(wo["p"]) and wo["p"] < 0.05) else " "
            print(f"  {e:>7}{ri:>8.1f}%{ri-bi:>+6.1f}{wi['p']:>7.3f}{si} | "
                  f"{ro:>6.1f}%{ro-bo:>+6.1f}{wo['p']:>7.3f}{so}")


if __name__ == "__main__":
    main()
