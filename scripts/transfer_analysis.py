#!/usr/bin/env python3
"""transfer_analysis.py — cross-pattern transfer matrix.

Asks: if a model is faithful on category A, is it also faithful on category B?
Computes a per-(model, category) success matrix, then a 7x7 category-correlation
matrix across models. Reveals whether optimization capability is a single
underlying skill (high cross-category correlation) or category-specific
(low or negative correlation).

The cell (A, B) is the Spearman rank correlation across models of their
faithful-rate on category A vs their faithful-rate on category B. Strong
positive correlation (> 0.7) means "models good at A tend to be good at B";
near-zero or negative correlation means "skill in A says little about skill
in B" — which is the more interesting result for benchmark interpretation.

Usage:
    python3 scripts/transfer_analysis.py results.csv [--out figs/transfer.pdf]
                                           [--metric faithful|pass1|speedup]
                                           [--strategy STRATEGY]
                                           [--min-models N]
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

_CATEGORIES = ["Semantic Redundancy", "Input-Sensitive", "Control-Flow",
               "Human-style", "Data Structure", "Algorithmic", "Memory-IO"]
_CAT_SHORT = ["SR", "IS", "CF", "HR", "DS", "AL", "MI"]


def _category_short(full_or_code: str) -> str:
    """Map full category names or pattern_id prefixes to 2-letter codes."""
    if not isinstance(full_or_code, str):
        return ""
    s = full_or_code.strip()
    # Try pattern_id prefix first (e.g. "SR-1" -> "SR", "HO-AL-1" -> "AL")
    if "-" in s:
        parts = s.split("-")
        for part in parts:
            if part in _CAT_SHORT:
                return part
    # Try full category name
    lower = s.lower()
    if "semantic" in lower or "redundan" in lower: return "SR"
    if "input" in lower:                            return "IS"
    if "control" in lower:                          return "CF"
    if "human" in lower:                            return "HR"
    if "data structure" in lower or "data-struct" in lower: return "DS"
    if "algorithm" in lower:                        return "AL"
    if "memory" in lower or "io" in lower:          return "MI"
    return ""


def _per_model_category_rate(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Return DataFrame indexed by model, with one column per category."""
    df = df.copy()
    df["cat_short"] = df.get("category", df.get("pattern_id", "")).map(_category_short)
    df = df[df["cat_short"].isin(_CAT_SHORT)]
    if df.empty:
        return pd.DataFrame()

    if metric == "faithful":
        if "faithfulness_cell" not in df.columns:
            print("ERROR: --metric faithful requires faithfulness_cell column "
                  "(run evaluate.py with --faithfulness).", file=sys.stderr)
            sys.exit(2)
        df["_score"] = (df["faithfulness_cell"]
                        .fillna("")
                        .astype(str)
                        .isin({"FAITHFUL", "FAITHFUL_ALTERNATIVE"})
                        .astype(float))
    elif metric == "pass1":
        df["_score"] = (df.get("correct", False).astype(bool)
                        & ~df.get("unreliable", False).astype(bool)).astype(float)
    elif metric == "speedup":
        # geomean speedup over correct+not-unreliable rows
        df = df[df.get("correct", False).astype(bool)
                & ~df.get("unreliable", False).astype(bool)
                & (df.get("speedup_vs_slow", 0) > 0)]
        if df.empty:
            return pd.DataFrame()
        df["_score"] = df["speedup_vs_slow"].apply(math.log)
    else:
        raise ValueError(f"unknown metric: {metric}")

    pivot = (df.groupby(["model", "cat_short"])["_score"]
             .mean()
             .unstack("cat_short"))
    if metric == "speedup":
        # Convert log back to geometric mean
        pivot = pivot.applymap(math.exp)
    # Re-order columns to canonical taxonomy order
    pivot = pivot.reindex(columns=_CAT_SHORT)
    return pivot


def _correlation_matrix(rates: pd.DataFrame, method: str = "spearman") -> pd.DataFrame:
    """Compute correlation between categories across models."""
    return rates.corr(method=method, min_periods=2)


def _plot_heatmap(corr: pd.DataFrame, out_path: str, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", center=0,
                cmap="RdBu_r", vmin=-1, vmax=1, square=True,
                cbar_kws={"label": "Spearman correlation across models"},
                ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Category B")
    ax.set_ylabel("Category A")
    plt.tight_layout()
    plt.savefig(out_path)
    if out_path.lower().endswith(".pdf"):
        png = out_path[:-4] + ".png"
        plt.savefig(png, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("results_csv")
    parser.add_argument("--out", default="figs/transfer.pdf")
    parser.add_argument("--metric", default="faithful",
                        choices=["faithful", "pass1", "speedup"])
    parser.add_argument("--strategy", default=None,
                        help="Filter to one prompting strategy")
    parser.add_argument("--min-models", type=int, default=3,
                        help="Minimum number of models contributing to each "
                             "category pair (default 3 — Spearman needs >=2 "
                             "to be defined; 3 gives a meaningful number).")
    parser.add_argument("--held-out-only", action="store_true",
                        help="Restrict to held-out patterns (pattern_id "
                             "prefix 'HO-'). For the fine-tuning transfer "
                             "experiment: shows whether category-skill "
                             "transfers across held-out patterns only.")
    parser.add_argument("--exclude-held-out", action="store_true",
                        help="Restrict to base-set patterns (excludes "
                             "pattern_id prefix 'HO-'). Mutually exclusive "
                             "with --held-out-only.")
    args = parser.parse_args()
    if args.held_out_only and args.exclude_held_out:
        parser.error("--held-out-only and --exclude-held-out are mutually exclusive")

    if not os.path.exists(args.results_csv):
        print(f"no data to analyze (file not found: {args.results_csv})")
        return
    try:
        df = pd.read_csv(args.results_csv)
    except (pd.errors.EmptyDataError, FileNotFoundError):
        print(f"no data to analyze (empty: {args.results_csv})")
        return

    if df.empty:
        print(f"no data to analyze (zero rows: {args.results_csv})")
        return

    if args.strategy:
        df = df[df.get("strategy", "") == args.strategy]
        if df.empty:
            print(f"no data after --strategy {args.strategy} filter")
            return

    if args.held_out_only:
        df = df[df.get("pattern_id", "").astype(str).str.startswith("HO-")]
        if df.empty:
            print("no held-out rows in input")
            return
        print(f"[held-out-only filter] {len(df)} rows on held-out patterns")
    elif args.exclude_held_out:
        df = df[~df.get("pattern_id", "").astype(str).str.startswith("HO-")]
        if df.empty:
            print("no base-set rows in input")
            return
        print(f"[base-set filter] {len(df)} rows on non-held-out patterns")

    rates = _per_model_category_rate(df, args.metric)
    if rates.empty or len(rates) < args.min_models:
        n = len(rates)
        print(f"only {n} model(s) with usable data — need >= {args.min_models} "
              f"for correlation analysis. Run more models first.")
        return

    print(f"Per-(model, category) {args.metric} rates ({len(rates)} models):")
    print()
    print(rates.round(3).to_string())
    print()

    corr = _correlation_matrix(rates, method="spearman")
    print(f"Cross-category Spearman correlation ({args.metric}):")
    print(corr.round(2).to_string())
    print()

    # Surface notable findings
    strong_pos = []
    strong_neg = []
    near_zero = []
    for i, a in enumerate(corr.columns):
        for b in corr.columns[i + 1:]:
            v = corr.loc[a, b]
            if pd.isna(v):
                continue
            if v > 0.7:
                strong_pos.append((a, b, v))
            elif v < -0.3:
                strong_neg.append((a, b, v))
            elif abs(v) < 0.2:
                near_zero.append((a, b, v))

    if strong_pos:
        print("STRONG POSITIVE (>0.7) — skill transfers between these categories:")
        for a, b, v in sorted(strong_pos, key=lambda x: -x[2]):
            print(f"  {a} <-> {b}:  rho = {v:+.2f}")
    if strong_neg:
        print()
        print("STRONG NEGATIVE (<-0.3) — skill in one anti-correlates with the other:")
        for a, b, v in sorted(strong_neg, key=lambda x: x[2]):
            print(f"  {a} <-> {b}:  rho = {v:+.2f}")
    if near_zero:
        print()
        print("NEAR-ZERO (|rho|<0.2) — independent capability axes:")
        for a, b, v in sorted(near_zero, key=lambda x: abs(x[2])):
            print(f"  {a} <-> {b}:  rho = {v:+.2f}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    title = f"Cross-pattern transfer ({args.metric}, n={len(rates)} models)"
    if args.strategy:
        title += f"\nstrategy: {args.strategy}"
    _plot_heatmap(corr, args.out, title)
    print()
    print(f"Wrote heatmap: {args.out}")
    if args.out.lower().endswith(".pdf"):
        print(f"Wrote heatmap: {args.out[:-4]}.png")


if __name__ == "__main__":
    main()
