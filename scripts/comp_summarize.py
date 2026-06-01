"""COMP-variant performance vs single-pattern baselines.

Reads a results CSV (typically from ``--dataset dataset`` with COMP variants
included) and computes the "composition gap" for each model: the difference
between single-pattern pass@1 and COMP pass@1, broken down by composition.

For each COMP variant we read ``dataset/COMP/<vid>/metadata.json`` to look
up its ``composition`` (a list of constituent pattern IDs). We then compute:
  * single-pattern pass@1 for each constituent (averaged over its rows)
  * the geomean of constituent pass@1s (as an "expected" composed baseline)
  * the actual COMP variant pass@1
  * composition gap = expected - actual (positive = worse than expected)

Usage:
    python3 scripts/comp_summarize.py results.csv [--out comp_results.csv] \\
        [--dataset-dir dataset] [--strategy STRATEGY]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def _load_comp_compositions(dataset_dir: str) -> dict[str, list[str]]:
    """variant_id → list[pattern_id]. Empty dict if dataset/COMP missing."""
    out: dict[str, list[str]] = {}
    comp_dir = os.path.join(dataset_dir, "COMP")
    if not os.path.isdir(comp_dir):
        return out
    for vid in os.listdir(comp_dir):
        meta_p = os.path.join(comp_dir, vid, "metadata.json")
        if not os.path.exists(meta_p):
            continue
        try:
            with open(meta_p) as f:
                meta = json.load(f)
            comp = meta.get("composition")
            if isinstance(comp, list):
                out[meta.get("variant_id", vid)] = list(comp)
        except (OSError, json.JSONDecodeError):
            continue
    return out


def _is_correct(row: pd.Series) -> bool:
    return bool(row.get("correct")) and not bool(row.get("unreliable"))


def _geomean(xs: list[float]) -> float:
    xs = [x for x in xs if x is not None and not np.isnan(x) and x > 0]
    if not xs:
        return float("nan")
    return float(np.exp(np.mean(np.log(xs))))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dataset-dir", default="dataset",
                    help="Where to find dataset/COMP/<vid>/metadata.json")
    ap.add_argument("--strategy", default=None)
    args = ap.parse_args()

    if not os.path.exists(args.csv) or os.path.getsize(args.csv) == 0:
        print("no data to analyze")
        return 0
    df = pd.read_csv(args.csv)
    if len(df) == 0:
        print("no data to analyze")
        return 0
    if args.strategy:
        df = df[df["strategy"] == args.strategy]
        if len(df) == 0:
            print(f"no rows with strategy={args.strategy}")
            return 0

    df = df.copy()
    df["ok"] = df.apply(_is_correct, axis=1)

    comp_df = df[df["pattern_id"] == "COMP"].copy()
    if len(comp_df) == 0:
        print("no COMP rows in CSV — nothing to summarize")
        return 0

    compositions = _load_comp_compositions(args.dataset_dir)
    if not compositions:
        print(f"warn: no compositions loaded from {args.dataset_dir}/COMP; "
              "headline gap will use unweighted COMP vs single-pattern pass@1")

    # Single-pattern pass@1 per (model, pattern_id), excluding COMP rows.
    single = df[df["pattern_id"] != "COMP"]
    sp_table = single.groupby(["model", "pattern_id"])["ok"].mean()

    # ── Per-row record: one row per (model, COMP variant) ─────────────────
    records = []
    for (model, vid), grp in comp_df.groupby(["model", "variant_id"]):
        actual = float(grp["ok"].mean())
        comp = compositions.get(str(vid), [])
        const_pass1 = [float(sp_table.get((model, pid), float("nan")))
                       for pid in comp]
        expected = _geomean(const_pass1) if const_pass1 else float("nan")
        records.append({
            "model": model,
            "variant_id": vid,
            "composition": "+".join(comp) if comp else "(unknown)",
            "n_samples": len(grp),
            "comp_pass1": actual,
            "expected_geomean": expected,
            "gap": (expected - actual) if not np.isnan(expected) else float("nan"),
        })
    per_variant = pd.DataFrame(records)

    # ── Per-model rollup ──────────────────────────────────────────────────
    print("\n=== Per-model composition gap (single-pattern vs COMP pass@1) ===")
    single_overall = single.groupby("model")["ok"].mean().rename("single_pass1")
    comp_overall = comp_df.groupby("model")["ok"].mean().rename("comp_pass1")
    roll = pd.concat([single_overall, comp_overall], axis=1)
    roll["gap_pp"] = (roll["single_pass1"] - roll["comp_pass1"]) * 100
    roll["single_pass1"] *= 100
    roll["comp_pass1"] *= 100
    print(roll.to_string(float_format=lambda x: f"{x:6.2f}"))

    avg_single = float(roll["single_pass1"].mean(skipna=True))
    avg_comp = float(roll["comp_pass1"].mean(skipna=True))
    print(f"\nHeadline: Models score {avg_single:.1f}% on single-pattern, "
          f"{avg_comp:.1f}% on COMP — composition gap is "
          f"{avg_single - avg_comp:.1f} percentage points (averaged over models).")

    # ── Easiest / hardest COMP variants per model ─────────────────────────
    if len(per_variant):
        print("\n=== Easiest COMP variants per model ===")
        for model, mg in per_variant.groupby("model"):
            mg = mg.sort_values("comp_pass1", ascending=False)
            top = mg.head(3)
            bot = mg.tail(3)
            print(f"\n{model}")
            for _, r in top.iterrows():
                print(f"  EASIEST  {r['variant_id']:14s}  "
                      f"{r['composition']:30s}  pass@1={r['comp_pass1']*100:5.1f}%")
            for _, r in bot.iterrows():
                print(f"  HARDEST  {r['variant_id']:14s}  "
                      f"{r['composition']:30s}  pass@1={r['comp_pass1']*100:5.1f}%")

    if args.out:
        per_variant.to_csv(args.out, index=False)
        print(f"\nwrote {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
