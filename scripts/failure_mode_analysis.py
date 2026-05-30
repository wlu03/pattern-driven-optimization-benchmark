"""Failure-mode breakdown for runs with ``--faithfulness`` on.

Tabulates the 2x2 cell distribution per (model, category) and surfaces two
specifically-interesting failure modes:

* STRUCTURAL_ONLY rate per category — model recognized the pattern but broke
  correctness, the most useful "knows the shape but can't land it" signal.
* FAITHFUL_ALTERNATIVE rate per category — model found a valid non-expected
  transformation, the most useful "creativity > template-matching" signal.

Usage:
    python3 scripts/failure_mode_analysis.py results.csv \\
        [--out failure_modes.csv] [--strategy STRATEGY]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from pdob_core.patterns import PATTERNS  # noqa: E402


_CELLS = ["FAITHFUL", "FAITHFUL_ALTERNATIVE", "STRUCTURAL_ONLY", "FAILED"]
_PID_TO_CAT = {p.pattern_id: p.pattern_id.split("-")[0] for p in PATTERNS}


def _cell_value(x) -> str:
    if x in _CELLS:
        return x
    return "n/a-not-run"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default=None,
                    help="Optional CSV path for the model x cell counts table.")
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
            print(f"no data to analyze (strategy={args.strategy})")
            return 0

    if "faithfulness_cell" not in df.columns:
        print("no faithfulness_cell column — re-run with --faithfulness")
        return 0

    df = df.copy()
    df["cell"] = df["faithfulness_cell"].apply(_cell_value)
    df["category"] = df["pattern_id"].map(_PID_TO_CAT).fillna(df["pattern_id"])

    # ── 1. Per-model cell distribution ────────────────────────────────────
    print("\n=== Per-model cell distribution ===")
    pivot = df.pivot_table(index="model", columns="cell",
                           values="pattern_id", aggfunc="count",
                           fill_value=0)
    for cell in _CELLS + ["n/a-not-run"]:
        if cell not in pivot.columns:
            pivot[cell] = 0
    pivot = pivot[_CELLS + ["n/a-not-run"]]
    pivot["total"] = pivot.sum(axis=1)
    pct = pivot.div(pivot["total"], axis=0) * 100
    pct.columns = [f"{c}_%" for c in pct.columns]
    combined = pd.concat([pivot, pct.drop(columns=["total_%"])], axis=1)
    print(combined.to_string(float_format=lambda x: f"{x:6.1f}"))

    if args.out:
        combined.to_csv(args.out)
        print(f"\nwrote {args.out}")

    # ── 2. STRUCTURAL_ONLY rate per category (knew shape, broke correctness) ─
    print("\n=== STRUCTURAL_ONLY rate per (model, category) "
          "[model recognized pattern but broke correctness] ===")
    so_pivot = df.assign(is_so=(df["cell"] == "STRUCTURAL_ONLY")).pivot_table(
        index="model", columns="category", values="is_so",
        aggfunc="mean", fill_value=0.0,
    ) * 100
    print(so_pivot.to_string(float_format=lambda x: f"{x:5.1f}%"))

    # ── 3. FAITHFUL_ALTERNATIVE rate per category (creative & correct) ────
    print("\n=== FAITHFUL_ALTERNATIVE rate per (model, category) "
          "[model found valid alternative transformation] ===")
    fa_pivot = df.assign(is_fa=(df["cell"] == "FAITHFUL_ALTERNATIVE")).pivot_table(
        index="model", columns="category", values="is_fa",
        aggfunc="mean", fill_value=0.0,
    ) * 100
    print(fa_pivot.to_string(float_format=lambda x: f"{x:5.1f}%"))

    # Highest-STRUCTURAL_ONLY (model, category) cells globally — likely the
    # paper's "model knows the trick but breaks the data dependency" exhibit.
    so_stack = so_pivot.stack().sort_values(ascending=False)
    if len(so_stack):
        print("\nTop-5 STRUCTURAL_ONLY (model, category) cells:")
        for (m, c), v in so_stack.head(5).items():
            print(f"  {m:35s}  category={c:3s}  {v:.1f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
