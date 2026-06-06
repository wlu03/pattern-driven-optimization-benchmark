#!/usr/bin/env python3
"""Memory-safe model ranking from per-cell scored CSVs.

The earlier ranking pass loaded every column of all 30 scored CSVs and
concatenated them. The reasoning models carry a ``reasoning_trace`` column of
17k+ chars/row; in pandas object dtype that balloons several-fold and the
``pd.concat`` copies it all again -> the run OOM'd.

This script reads ONLY the five columns ranking needs (``usecols``), one file
at a time, computes each cell's summary immediately, then drops the frame. It
never concatenates raw rows, so peak RAM is ~0.16 MB regardless of trace size.

Metric matches scripts/scaling_analysis.py exactly:
  * geomean speedup = geometric mean of ``speedup_vs_slow`` over rows with
    ``correct == True`` AND ``unreliable != True``
  * pass@1          = that same mask's rate over all variants in the cell
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from pdob_core.model_metadata import get_metadata  # noqa: E402

# Only these five columns are read from disk. Everything else (llm_code,
# reasoning_trace, faithfulness_*, unreliable_reason) is left on disk.
NEEDED = ["model", "strategy", "correct", "unreliable", "speedup_vs_slow"]
STRATS = ["generic", "pattern-aware", "taxonomy-guided"]
SCORED_GLOB = "results/pareto/*_scored.csv"


def _as_bool(s: pd.Series) -> pd.Series:
    """Coerce a column to clean bool (handles real bools, strings, NaN)."""
    if s.dtype == bool:
        return s
    if s.dtype == object:
        return s.astype(str).str.strip().str.lower().isin(("true", "1", "yes"))
    return s.fillna(0).astype(bool)


def _geomean(xs: np.ndarray) -> float:
    xs = np.asarray(xs, dtype=float)
    xs = xs[xs > 0]
    return float(np.exp(np.mean(np.log(xs)))) if xs.size else float("nan")


def _kind(model_id: str, reasoning: bool) -> str:
    mid = model_id.lower()
    if "coder" in mid or "codestral" in mid:
        return "coder"
    if reasoning:
        return "reasoning"
    return "general"


def collect() -> pd.DataFrame:
    """One row per (model, strategy) cell. Streams files; tiny peak memory."""
    cells: list[dict] = []
    for f in sorted(glob.glob(SCORED_GLOB)):
        # usecols is the whole game: never materialize the giant text columns.
        df = pd.read_csv(
            f,
            usecols=lambda c: c in NEEDED,
            dtype={"speedup_vs_slow": "float32"},
        )
        if "model" not in df.columns or not len(df):
            del df
            continue
        ok = _as_bool(df["correct"])
        if "unreliable" in df.columns:
            ok &= ~_as_bool(df["unreliable"])
        df = df.assign(_ok=ok)
        for (model, strat), g in df.groupby(["model", "strategy"], sort=False):
            okrows = g[g["_ok"]]
            sp = okrows["speedup_vs_slow"].to_numpy(dtype=float)
            cells.append(
                {
                    "model": model,
                    "strategy": strat,
                    "n": int(len(g)),
                    "n_ok": int(len(okrows)),
                    "pass1": len(okrows) / len(g) if len(g) else float("nan"),
                    "geomean": _geomean(sp),
                    "best": float(np.nanmax(sp)) if sp.size else float("nan"),
                }
            )
        del df, ok  # free before next file -> peak stays ~one file's 5 cols
    return pd.DataFrame(cells)


def _fmt_triplet(cell_by_strat: dict, key: str, pct: bool = False) -> str:
    out = []
    for s in STRATS:
        v = cell_by_strat.get(s, {}).get(key)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            out.append("—")
        elif pct:
            out.append(f"{round(v * 100):d}")
        else:
            out.append(f"{v:.1f}")
    return " / ".join(out)


def build_table(cells: pd.DataFrame, drop_zero: bool) -> pd.DataFrame:
    rows = []
    for model, mdf in cells.groupby("model", sort=False):
        by_strat = {r["strategy"]: r for _, r in mdf.iterrows()}
        meta = get_metadata(model)
        params = meta.param_count_b
        geos = [by_strat.get(s, {}).get("geomean", float("nan")) for s in STRATS]
        bests = [by_strat.get(s, {}).get("best", float("nan")) for s in STRATS]
        peak = float(np.nanmax(bests)) if not all(np.isnan(bests)) else float("nan")
        peak_geo = float(np.nanmax(geos)) if not all(np.isnan(geos)) else float("nan")
        all_zero = np.nansum(geos) == 0 or np.isnan(peak_geo)
        rows.append(
            {
                "model": model,
                "params": params if params is not None else float("nan"),
                "type": _kind(model, meta.reasoning),
                "pass1": _fmt_triplet(by_strat, "pass1", pct=True),
                "geomean": _fmt_triplet(by_strat, "geomean"),
                "peak_geo": peak_geo,
                "peak": peak,
                "all_zero": bool(all_zero),
            }
        )
    out = pd.DataFrame(rows)
    if drop_zero:
        bogus = out[out["all_zero"]]["model"].tolist()
        if bogus:
            print(f"[warn] excluding {len(bogus)} model(s) with all-zero scores "
                  f"(re-score never completed): {', '.join(bogus)}\n", file=sys.stderr)
        out = out[~out["all_zero"]].copy()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sort", choices=["size", "peak"], default="size",
                    help="rank by parameter count (default) or by peak geomean speedup")
    ap.add_argument("--keep-zero", action="store_true",
                    help="keep models whose scores are all zero (default: drop)")
    args = ap.parse_args()

    cells = collect()
    if cells.empty:
        print("no scored cells found under", SCORED_GLOB, file=sys.stderr)
        sys.exit(1)
    table = build_table(cells, drop_zero=not args.keep_zero)

    if args.sort == "size":
        table = table.sort_values("params", kind="stable", na_position="last")
    else:
        table = table.sort_values("peak_geo", ascending=False, kind="stable")

    # "Peak" = best of the three per-strategy geomeans (NOT raw max single-variant
    # speedup, which is dominated by timing-artifact outliers like 160000x).
    h = f"{'Model':<32}{'B':>5}  {'type':<10}{'pass@1 g/p/t':<18}{'geomean× g/p/t':<22}{'peak×':>7}"
    print(h)
    print("-" * len(h))
    for _, r in table.iterrows():
        b = "—" if np.isnan(r["params"]) else f"{r['params']:g}"
        peak = "—" if np.isnan(r["peak_geo"]) else f"{r['peak_geo']:.1f}×"
        print(f"{r['model']:<32}{b:>5}  {r['type']:<10}{r['pass1']:<18}{r['geomean']:<22}{peak:>7}")


if __name__ == "__main__":
    main()
