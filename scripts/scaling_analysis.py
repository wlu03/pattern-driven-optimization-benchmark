"""Scaling-laws plot for the PDOB benchmark.

Reads a CSV produced by ``scripts/evaluate.py`` and plots one of three
metrics against log10(param_count_b * 1e9), grouped by model family.

Usage:
    python3 scripts/scaling_analysis.py results.csv [--out scaling.pdf] \\
        [--strategy STRATEGY] [--metric geomean_speedup|pass1|faithful_rate]

If multiple ``--samples`` are present per (model, pattern) cell, plots
bootstrap 95% CI error bars (1000 resamples).
"""
from __future__ import annotations

import argparse
import math
import os
import sys

# Make repo root importable so ``pdob_core`` resolves when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from pdob_core.model_metadata import get_metadata  # noqa: E402


_FAMILY_COLORS = {
    "Claude":   "#cc785c",
    "GPT":      "#10a37f",
    "DeepSeek": "#4b3a8a",
    "Gemini":   "#4285f4",
    "Llama":    "#0668e1",
    "Qwen":     "#9b1c1c",
    "Mistral":  "#fa520f",
    "Gemma":    "#0f9d58",
    "Phi":      "#737373",
    "Falcon":   "#d4a017",
    "Unknown":  "#bbbbbb",
}


def _geomean(xs: np.ndarray) -> float:
    xs = xs[xs > 0]
    if len(xs) == 0:
        return float("nan")
    return float(np.exp(np.mean(np.log(xs))))


def _compute_metric(group: pd.DataFrame, metric: str) -> float:
    if metric == "geomean_speedup":
        valid = group[(group["correct"] == True) & (group["unreliable"] != True)]  # noqa: E712
        return _geomean(valid["speedup_vs_slow"].to_numpy(dtype=float))
    if metric == "pass1":
        ok = (group["correct"] == True) & (group["unreliable"] != True)  # noqa: E712
        return float(ok.mean()) if len(group) else float("nan")
    if metric == "faithful_rate":
        corr = group[group["correct"] == True]  # noqa: E712
        if len(corr) == 0 or "faithfulness_cell" not in corr.columns:
            return float("nan")
        return float((corr["faithfulness_cell"] == "FAITHFUL").mean())
    raise ValueError(f"Unknown metric: {metric}")


def _bootstrap_ci(group: pd.DataFrame, metric: str, n_boot: int = 1000,
                  rng: np.random.Generator | None = None) -> tuple[float, float]:
    """Return (lo, hi) 95% bootstrap CI for the metric, or (nan, nan) if N<3."""
    if rng is None:
        rng = np.random.default_rng(0xC0FFEE)
    n = len(group)
    if n < 3:
        return (float("nan"), float("nan"))
    vals = np.empty(n_boot, dtype=float)
    idx = group.index.to_numpy()
    for i in range(n_boot):
        sample = group.loc[rng.choice(idx, size=n, replace=True)]
        vals[i] = _compute_metric(sample, metric)
    vals = vals[~np.isnan(vals)]
    if len(vals) == 0:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals, 2.5)),
            float(np.percentile(vals, 97.5)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="results.csv from scripts/evaluate.py")
    ap.add_argument("--out", default="scaling.pdf",
                    help="Output file path (.pdf is created; .png alongside).")
    ap.add_argument("--strategy", default=None,
                    help="Filter to a single strategy (e.g. generic).")
    ap.add_argument("--metric", default="geomean_speedup",
                    choices=["geomean_speedup", "pass1", "faithful_rate"])
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
            print(f"no data to analyze (no rows with strategy={args.strategy})")
            return 0

    has_samples = "sample_idx" in df.columns and df["sample_idx"].nunique() > 1
    rng = np.random.default_rng(0xC0FFEE)

    rows = []
    for model_id, gm in df.groupby("model"):
        meta = get_metadata(model_id)
        if meta.param_count_b is None:
            print(f"warn: no param_count for model={model_id}; skipping")
            continue
        metric_val = _compute_metric(gm, args.metric)
        if has_samples:
            lo, hi = _bootstrap_ci(gm, args.metric, rng=rng)
        else:
            lo, hi = float("nan"), float("nan")
        rows.append({
            "model": model_id,
            "family": meta.family,
            "params": meta.param_count_b * 1e9,
            "metric": metric_val,
            "lo": lo,
            "hi": hi,
        })

    if not rows:
        print("no plottable rows (no models have known param counts)")
        return 0

    plot_df = pd.DataFrame(rows).dropna(subset=["metric"])
    if len(plot_df) == 0:
        print("all models have NaN metric; nothing to plot")
        return 0

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for family, fam_df in plot_df.groupby("family"):
        fam_df = fam_df.sort_values("params")
        color = _FAMILY_COLORS.get(family, "#666666")
        x = np.log10(fam_df["params"].to_numpy())
        y = fam_df["metric"].to_numpy()
        if has_samples:
            lo = fam_df["lo"].to_numpy()
            hi = fam_df["hi"].to_numpy()
            yerr = np.vstack([np.clip(y - lo, 0, None), np.clip(hi - y, 0, None)])
            ax.errorbar(x, y, yerr=yerr, fmt="o-", color=color, label=family,
                        capsize=3, lw=1.5, ms=6)
        else:
            ax.plot(x, y, marker="o", color=color, label=family, lw=1.5, ms=6)
        for _, row in fam_df.iterrows():
            ax.annotate(row["model"], (math.log10(row["params"]), row["metric"]),
                        fontsize=6, alpha=0.55, xytext=(3, 3),
                        textcoords="offset points")

    if args.metric == "geomean_speedup":
        ax.set_yscale("log")
        ax.set_ylabel("Geometric mean speedup vs. slow (log scale)")
    elif args.metric == "pass1":
        ax.set_ylim(-0.02, 1.02)
        ax.set_ylabel("pass@1 (correct AND not unreliable)")
    else:
        ax.set_ylim(-0.02, 1.02)
        ax.set_ylabel("Faithful rate (FAITHFUL cell over correct attempts)")

    ax.set_xlabel("log10(parameter count)")
    title = f"Scaling: {args.metric}"
    if args.strategy:
        title += f"  •  strategy={args.strategy}"
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8, ncols=2)
    fig.tight_layout()

    out_pdf = args.out
    out_png = os.path.splitext(args.out)[0] + ".png"
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=160)
    plt.close(fig)
    print(f"saved {out_pdf} and {out_png} ({len(plot_df)} models plotted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
