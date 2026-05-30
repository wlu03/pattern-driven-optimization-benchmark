"""Per-(model, category) heatmap — the standard figure for code-eval papers.

Reads a CSV from ``scripts/evaluate.py`` and renders one cell per
(model x 7 categories) with the chosen metric. Rows sort by family then
parameter count (smaller first, so the eye scans up toward the larger
models near the bottom).

Usage:
    python3 scripts/category_heatmap.py results.csv [--out heatmap.pdf] \\
        [--strategy STRATEGY] [--metric geomean_speedup|pass1|faithful_rate]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

from pdob_core.patterns import PATTERNS  # noqa: E402
from pdob_core.model_metadata import get_metadata  # noqa: E402


# Category short-code → full label (so heatmap columns stay narrow).
_CATEGORY_ORDER = ["SR", "IS", "CF", "HR", "DS", "AL", "MI"]
_CATEGORY_FULL = {
    "SR": "Semantic Redundancy",
    "IS": "Input-Sensitive Inefficiency",
    "CF": "Control-Flow",
    "HR": "Human-Style Antipatterns",
    "DS": "Data Structure",
    "AL": "Algorithmic",
    "MI": "Memory/IO",
}
# Map ``pattern_id`` prefix → bucket. COMP rows are folded into a special
# "COMP" column only if the user passes --include-comp (off by default).
_PID_TO_CAT = {p.pattern_id: p.pattern_id.split("-")[0] for p in PATTERNS}


def _geomean(xs: np.ndarray) -> float:
    xs = xs[xs > 0]
    if len(xs) == 0:
        return float("nan")
    return float(np.exp(np.mean(np.log(xs))))


def _cell_metric(group: pd.DataFrame, metric: str) -> float:
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


def _format_cell(val: float, metric: str) -> str:
    if np.isnan(val):
        return ""
    if metric == "geomean_speedup":
        return f"{val:.1f}x"
    return f"{val * 100:.0f}%"


def _sort_models(models: list[str]) -> list[str]:
    def key(m: str):
        meta = get_metadata(m)
        return (meta.family, meta.param_count_b or 0.0, m)
    return sorted(models, key=key)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="heatmap.pdf")
    ap.add_argument("--strategy", default=None)
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
            print(f"no data to analyze (strategy={args.strategy})")
            return 0

    df = df.copy()
    df["category_short"] = df["pattern_id"].map(_PID_TO_CAT)
    df = df[df["category_short"].isin(_CATEGORY_ORDER)]
    if len(df) == 0:
        print("no rows with recognized category prefix")
        return 0

    models = _sort_models(sorted(df["model"].unique()))
    mat = np.full((len(models), len(_CATEGORY_ORDER)), np.nan, dtype=float)
    for i, m in enumerate(models):
        for j, cat in enumerate(_CATEGORY_ORDER):
            sub = df[(df["model"] == m) & (df["category_short"] == cat)]
            if len(sub):
                mat[i, j] = _cell_metric(sub, args.metric)

    annots = np.array([[_format_cell(mat[i, j], args.metric)
                        for j in range(mat.shape[1])]
                       for i in range(mat.shape[0])])

    # Log-scale color for speedups (huge dynamic range); linear 0-1 for rates.
    if args.metric == "geomean_speedup":
        with np.errstate(invalid="ignore"):
            plot_mat = np.log10(np.where(mat > 0, mat, np.nan))
        cmap = "viridis"
        cbar_label = "log10(geomean speedup)"
    else:
        plot_mat = mat
        cmap = "RdYlGn"
        cbar_label = "pass@1" if args.metric == "pass1" else "Faithful rate"

    fig_h = max(3.0, 0.32 * len(models) + 1.5)
    fig, ax = plt.subplots(figsize=(8, fig_h))
    sns.heatmap(
        plot_mat,
        annot=annots,
        fmt="",
        cmap=cmap,
        ax=ax,
        xticklabels=[_CATEGORY_FULL[c] for c in _CATEGORY_ORDER],
        yticklabels=models,
        cbar_kws={"label": cbar_label},
        linewidths=0.4,
        linecolor="white",
        annot_kws={"size": 8},
    )
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    title = f"Per-category {args.metric}"
    if args.strategy:
        title += f"  •  strategy={args.strategy}"
    ax.set_title(title)
    fig.tight_layout()

    out_pdf = args.out
    out_png = os.path.splitext(args.out)[0] + ".png"
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=160)
    plt.close(fig)
    print(f"saved {out_pdf} and {out_png} "
          f"({len(models)} models x {len(_CATEGORY_ORDER)} cats)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
