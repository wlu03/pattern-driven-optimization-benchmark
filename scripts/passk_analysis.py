"""pass@k curves for runs with ``--samples k`` > 1.

Uses the standard unbiased estimator (Chen et al., 2021):

    pass@k = 1 - C(n - c, k) / C(n, k)

where ``n`` is the total number of samples per (model, problem) cell and
``c`` is the number of correct samples. Aggregation is the mean over
problems (one cell per (model, pattern_id, variant_id) when variants are
present; otherwise (model, pattern_id)).

Usage:
    python3 scripts/passk_analysis.py results.csv [--out passk.pdf] \\
        [--strategy STRATEGY] [--metric correct|faithful]
"""
from __future__ import annotations

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def _passk_unbiased(n: int, c: int, k: int) -> float:
    """Standard Codex pass@k estimator. Returns NaN for k>n."""
    if k > n or n <= 0:
        return float("nan")
    if n - c < k:
        return 1.0
    # 1 - C(n-c, k) / C(n, k) computed numerically-stably as a product.
    num = 1.0
    for i in range(k):
        num *= (n - c - i) / (n - i)
    return 1.0 - num


def _is_success(row: pd.Series, metric: str) -> bool:
    if metric == "correct":
        return bool(row.get("correct")) and not bool(row.get("unreliable"))
    if metric == "faithful":
        return row.get("faithfulness_cell") == "FAITHFUL"
    raise ValueError(f"Unknown metric: {metric}")


def _problem_key(row: pd.Series) -> tuple:
    vid = row.get("variant_id")
    if pd.isna(vid) or vid in (None, ""):
        return (row["model"], row["pattern_id"])
    return (row["model"], row["pattern_id"], vid)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="passk.pdf")
    ap.add_argument("--strategy", default=None)
    ap.add_argument("--metric", default="correct",
                    choices=["correct", "faithful"])
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
    df["success"] = df.apply(lambda r: _is_success(r, args.metric), axis=1)
    df["pkey"] = df.apply(_problem_key, axis=1)

    # Per (model, problem): n = sample count, c = success count.
    cells = df.groupby(["model", "pkey"]).agg(
        n=("success", "count"),
        c=("success", "sum"),
    ).reset_index()
    if len(cells) == 0:
        print("no data after grouping")
        return 0

    max_k = int(cells["n"].max())
    if max_k <= 1:
        print("max samples per cell = 1; pass@1 only:")
        p1 = (cells.assign(p1=cells["c"] / cells["n"])
                 .groupby("model")["p1"].mean() * 100)
        print(p1.to_frame("pass@1 (%)").to_string(
            float_format=lambda x: f"{x:6.2f}"))
        return 0

    # Per-(model, k): mean over problems of pass@k.
    rows = []
    for model, mg in cells.groupby("model"):
        for k in range(1, max_k + 1):
            vals = [_passk_unbiased(int(n), int(c), k)
                    for n, c in zip(mg["n"], mg["c"])]
            vals = [v for v in vals if not math.isnan(v)]
            if not vals:
                continue
            rows.append({"model": model, "k": k, "passk": np.mean(vals)})

    if not rows:
        print("no pass@k values computable")
        return 0
    plot_df = pd.DataFrame(rows)

    # Table.
    table = plot_df.pivot(index="model", columns="k", values="passk") * 100
    table.columns = [f"pass@{k}" for k in table.columns]
    print("\n=== pass@k per model (%) ===")
    print(table.to_string(float_format=lambda x: f"{x:6.2f}"))

    # Plot one curve per model.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for model, mg in plot_df.groupby("model"):
        mg = mg.sort_values("k")
        ax.plot(mg["k"], mg["passk"], marker="o", label=model, lw=1.4, ms=5)
    ax.set_xlabel("k")
    ax.set_ylabel(f"pass@k ({args.metric})")
    ax.set_xticks(range(1, max_k + 1))
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=7, ncols=2)
    title = "pass@k curves"
    if args.strategy:
        title += f"  •  strategy={args.strategy}"
    ax.set_title(title)
    fig.tight_layout()

    out_pdf = args.out
    out_png = os.path.splitext(args.out)[0] + ".png"
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=160)
    plt.close(fig)
    print(f"\nsaved {out_pdf} and {out_png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
