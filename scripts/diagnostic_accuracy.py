"""Diagnostic-accuracy analysis for ``--strategy diagnosis`` runs.

The diagnosis strategy asks the model to describe the inefficiency without
fixing it. The model's response lives in the ``llm_code`` column (we call
that field "code" but it's free text for this strategy). We keyword-match
the response against per-pattern phrases and aggregate.

Optional cross-tab: if you pass ``--impl-csv RESULTS.csv`` pointing at a
non-diagnosis run, we compute pass@1 for the same (model, category) cells
and report the (diag-accuracy, impl-accuracy) joint distribution. The
interesting cells are the off-diagonal ones — models that talk a good game
but can't fix the code, or vice versa.

Usage:
    python3 scripts/diagnostic_accuracy.py results.csv [--out diag.csv] \\
        [--strategy diagnosis] [--impl-csv impl_results.csv]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from pdob_core.patterns import PATTERNS  # noqa: E402


_PID_TO_CAT = {p.pattern_id: p.pattern_id.split("-")[0] for p in PATTERNS}


# Per-pattern phrase set. "Hit" if ANY phrase appears (case-insensitive,
# whole-substring) in the model's textual response. Phrasing is liberal on
# purpose — diagnosis prompts elicit colloquial answers.
_PATTERN_KEYWORDS: dict[str, list[str]] = {
    "SR-1": ["loop-invariant", "loop invariant", "hoist", "log series",
             "invariant call", "expensive call", "outside the loop"],
    "SR-2": ["loop-invariant", "loop invariant", "hoist", "invariant term",
             "common subexpression", "outside the loop"],
    "SR-3": ["aggregation", "recomputation", "redundant aggregate",
             "running sum", "incremental update", "cache"],
    "SR-4": ["loop-invariant", "loop invariant", "hoist", "invariant function",
             "outside the loop"],
    "SR-5": ["loop-invariant", "loop invariant", "denominator", "reciprocal",
             "multiply by reciprocal", "divide once"],
    "IS-1": ["sparse", "sparsity", "zero entries", "skip zero", "non-zero"],
    "IS-2": ["skewed", "biased", "branch early", "skip", "common case"],
    "IS-3": ["early termination", "early exit", "break early", "short circuit",
             "found"],
    "IS-4": ["sorted", "sortedness", "monotonic", "binary search",
             "exploit order", "ordered"],
    "IS-5": ["alias", "aliasing", "restrict", "no overlap", "no-alias",
             "fast path"],
    "CF-3": ["vectorization", "vectoriz", "simd", "branch in loop",
             "branchless", "hoist branch"],
    "CF-4": ["function pointer", "indirect call", "dispatch",
             "devirtualiz", "inline"],
    "HR-2": ["copy-paste", "duplication", "duplicate", "fuse loops",
             "loop fusion", "redundant loop"],
    "HR-3": ["dead code", "debug code", "unused", "side-effect free",
             "no-op", "remove"],
    "HR-4": ["defensive", "redundant check", "bounds check",
             "guarded", "remove check"],
    "DS-1": ["linear search", "hash", "hashmap", "hashtable", "o(n)",
             "lookup"],
    "DS-2": ["allocation", "pre-allocate", "preallocate", "reserve",
             "amortized", "realloc"],
    "DS-3": ["pass by value", "pass-by-value", "copy", "reference",
             "pointer", "unnecessary copy"],
    "DS-4": ["aos", "soa", "array of struct", "struct of array",
             "cache", "stride", "layout"],
    "AL-1": ["memoization", "dynamic programming", "dp", "brute force",
             "exponential", "subproblem"],
    "AL-2": ["repeated sort", "sorted insertion", "insertion order",
             "maintain sorted", "binary insert"],
    "AL-3": ["kmp", "knuth-morris", "naive matching", "pattern matching",
             "string match", "prefix function"],
    "AL-4": ["dp", "dynamic programming", "recursive", "memoization",
             "grid path", "subproblem", "overlapping"],
    "MI-1": ["sliding window", "alloc in loop", "allocation in loop",
             "reuse buffer", "amortized"],
    "MI-2": ["zeroing", "memset", "redundant zero", "uninitialized",
             "calloc"],
    "MI-3": ["heap", "alloc", "malloc", "stack alloc", "in-loop allocation"],
    "MI-4": ["row major", "column major", "cache", "stride", "access pattern",
             "row-major", "column-major"],
}


# Phrases that name a CATEGORY (lower-case, partial OK).
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "SR": ["semantic redundancy", "redundant computation", "loop-invariant",
           "loop invariant", "hoist"],
    "IS": ["input-sensitive", "input sensitive", "sparse", "skewed",
           "early termination", "sorted input"],
    "CF": ["control flow", "control-flow", "branch", "vectoriz",
           "function pointer", "dispatch"],
    "HR": ["human-style", "human style", "antipattern", "copy-paste",
           "dead code", "defensive", "duplication"],
    "DS": ["data structure", "linear search", "hash", "allocation",
           "layout", "aos", "soa"],
    "AL": ["algorithmic", "complexity", "memoization", "dp",
           "dynamic programming", "kmp", "asymptotic"],
    "MI": ["memory", "i/o", "io", "sliding window", "memset",
           "cache", "row major", "column major"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower())


def _pattern_hit(text: str, pattern_id: str) -> bool:
    norm = _normalize(text)
    phrases = _PATTERN_KEYWORDS.get(pattern_id, [])
    return any(p in norm for p in phrases)


def _category_hit(text: str, category_short: str) -> bool:
    norm = _normalize(text)
    phrases = _CATEGORY_KEYWORDS.get(category_short, [])
    return any(p in norm for p in phrases)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--strategy", default="diagnosis")
    ap.add_argument("--out", default=None)
    ap.add_argument("--impl-csv", default=None,
                    help="Optional non-diagnosis results.csv for cross-tab.")
    args = ap.parse_args()

    if not os.path.exists(args.csv) or os.path.getsize(args.csv) == 0:
        print("no data to analyze")
        return 0
    df = pd.read_csv(args.csv)
    if len(df) == 0:
        print("no data to analyze")
        return 0
    df = df[df["strategy"] == args.strategy]
    if len(df) == 0:
        print(f"no rows with strategy={args.strategy}")
        return 0

    df = df.copy()
    df["category"] = df["pattern_id"].map(_PID_TO_CAT).fillna(df["pattern_id"])
    df["text"] = df["llm_code"].fillna("")
    df["pattern_hit"]  = df.apply(
        lambda r: _pattern_hit(r["text"], r["pattern_id"]), axis=1)
    df["category_hit"] = df.apply(
        lambda r: _category_hit(r["text"], r["category"]), axis=1)

    # ── Per-model diagnostic accuracy ─────────────────────────────────────
    per_model = df.groupby("model").agg(
        n=("pattern_id", "count"),
        pattern_acc=("pattern_hit", "mean"),
        category_acc=("category_hit", "mean"),
    )
    per_model["pattern_acc"]  *= 100
    per_model["category_acc"] *= 100
    print("\n=== Diagnostic accuracy (per model) ===")
    print(per_model.to_string(float_format=lambda x: f"{x:6.1f}"))

    # ── Per-(model, category) ─────────────────────────────────────────────
    per_cat = df.pivot_table(index="model", columns="category",
                             values="category_hit", aggfunc="mean") * 100
    print("\n=== Category-naming accuracy (per model x category) ===")
    print(per_cat.to_string(float_format=lambda x: f"{x:5.1f}%"))

    if args.out:
        per_model.to_csv(args.out)
        print(f"\nwrote {args.out}")

    # ── Optional cross-tab vs implementation accuracy ─────────────────────
    if args.impl_csv:
        if not os.path.exists(args.impl_csv):
            print(f"\nwarn: --impl-csv {args.impl_csv} not found")
            return 0
        impl = pd.read_csv(args.impl_csv)
        if len(impl) == 0:
            print("\nimpl CSV empty; skipping cross-tab")
            return 0
        impl = impl.copy()
        impl["category"] = impl["pattern_id"].map(_PID_TO_CAT).fillna(impl["pattern_id"])
        impl["ok"] = (impl["correct"] == True) & (impl["unreliable"] != True)  # noqa: E712
        impl_acc = impl.groupby(["model", "category"])["ok"].mean().mul(100).rename("impl_acc_%")
        diag_acc = df.groupby(["model", "category"])["category_hit"].mean().mul(100).rename("diag_acc_%")
        xtab = pd.concat([diag_acc, impl_acc], axis=1).reset_index().dropna()
        if len(xtab) == 0:
            print("\nno overlapping (model, category) cells between diag and impl CSVs")
            return 0
        xtab["gap"] = xtab["diag_acc_%"] - xtab["impl_acc_%"]
        print("\n=== Diagnosis vs implementation cross-tab "
              "(positive gap = talks > does) ===")
        print(xtab.sort_values("gap", ascending=False).to_string(
            index=False, float_format=lambda x: f"{x:5.1f}"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
