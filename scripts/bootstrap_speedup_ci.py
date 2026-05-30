#!/usr/bin/env python3
"""bootstrap_speedup_ci.py
---------------------------
Bootstrap a confidence interval on a speedup ratio from per-run timing
samples, and gate a speedup CLAIM on the lower CI bound exceeding 1.0.

Supports the §Statistical Methodology section of docs/implementation.tex:
single-shot wall-clock timing is not a defensible basis for a speedup claim
(Mytkowicz et al., ASPLOS 2009 — measurement bias up to 33% routine /
300% extreme from link order + UNIX env padding alone), so the harness
needs an explicit statistical gate.

Usage forms
-----------
(1) Two-file form:
    bootstrap_speedup_ci.py --slow-csv slow.csv --fast-csv fast.csv

(2) One-file form (rows contain both columns, e.g. from setup_randomization.sh):
    bootstrap_speedup_ci.py --runs-csv runs.csv \\
        --slow-col slow_ms --fast-col fast_ms

(3) Plain-text form (one timing per line):
    bootstrap_speedup_ci.py --slow-csv slow.txt --fast-csv fast.txt
"""
import argparse
import csv
import math
import random
import sys


def read_timings(path: str, col: str = None) -> list:
    """Read per-run timings from a CSV column or a one-per-line file."""
    timings = []
    with open(path) as f:
        first = f.read()
    # Try CSV parse first
    if "," in first.splitlines()[0] if first.strip() else False:
        try:
            for row in csv.DictReader(first.splitlines()):
                names = list(row.keys())
                if not names:
                    continue
                target = col or ("time_ms" if "time_ms" in names else names[0])
                if row.get(target):
                    try:
                        timings.append(float(row[target]))
                    except ValueError:
                        continue
            if timings:
                return timings
        except Exception:
            pass
    # Plain one-per-line fallback (skip blanks + #-comments)
    for line in first.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            timings.append(float(s.split(",")[0]))
        except ValueError:
            continue
    return timings


def median(xs: list) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    return s[n // 2] if n % 2 == 1 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def percentile(xs: list, p: float) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    k = (n - 1) * p / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)


def bootstrap_speedup_ci(slow_ms: list, fast_ms: list, *,
                         resamples: int = 10_000, ci: float = 95,
                         seed: int = 42) -> tuple:
    """Resample WITH replacement from both populations; compute speedup
    ratio of medians per resample; return (median_speedup, lo, hi).

    Standard practice: percentile-bootstrap CI on the ratio of medians.
    10,000 resamples is the conventional default (Efron & Tibshirani 1994).
    """
    rng = random.Random(seed)
    n_slow, n_fast = len(slow_ms), len(fast_ms)
    if n_slow < 2 or n_fast < 2:
        raise ValueError(
            f"need >= 2 samples each (got slow={n_slow}, fast={n_fast})")

    speedups = []
    for _ in range(resamples):
        sample_slow = [slow_ms[rng.randrange(n_slow)] for _ in range(n_slow)]
        sample_fast = [fast_ms[rng.randrange(n_fast)] for _ in range(n_fast)]
        s = median(sample_slow)
        f = median(sample_fast)
        if f > 0:
            speedups.append(s / f)
    if not speedups:
        raise ValueError("all fast-ms resamples were zero — bad input data")
    speedups.sort()
    alpha = (100 - ci) / 2.0
    return median(speedups), percentile(speedups, alpha), \
           percentile(speedups, 100 - alpha)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slow-csv")
    parser.add_argument("--fast-csv")
    parser.add_argument("--runs-csv",
                        help="Single CSV with both slow_col and fast_col")
    parser.add_argument("--slow-col", default="slow_ms")
    parser.add_argument("--fast-col", default="fast_ms")
    parser.add_argument("--resamples", type=int, default=10_000)
    parser.add_argument("--ci", type=float, default=95.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gate", type=float, default=1.0,
                        help="Exit non-zero if lower CI bound <= GATE "
                             "(default 1.0 — claim a speedup only if CI "
                             "excludes no-effect)")
    args = parser.parse_args()

    if args.runs_csv:
        slow = read_timings(args.runs_csv, args.slow_col)
        fast = read_timings(args.runs_csv, args.fast_col)
    elif args.slow_csv and args.fast_csv:
        slow = read_timings(args.slow_csv)
        fast = read_timings(args.fast_csv)
    else:
        parser.error("provide either --runs-csv or both --slow-csv and --fast-csv")

    if not slow or not fast:
        print(f"ERROR: read 0 timings ({len(slow)} slow, {len(fast)} fast)",
              file=sys.stderr)
        sys.exit(2)

    print(f"Slow timings: n={len(slow)}  median={median(slow):.3f} ms  "
          f"IQR=[{percentile(slow, 25):.3f}, {percentile(slow, 75):.3f}]")
    print(f"Fast timings: n={len(fast)}  median={median(fast):.3f} ms  "
          f"IQR=[{percentile(fast, 25):.3f}, {percentile(fast, 75):.3f}]")

    sp_med, sp_lo, sp_hi = bootstrap_speedup_ci(
        slow, fast,
        resamples=args.resamples, ci=args.ci, seed=args.seed,
    )
    print()
    print(f"Bootstrap speedup ({int(args.ci)}% CI, {args.resamples} resamples):")
    print(f"  median = {sp_med:.3f}x")
    print(f"  CI     = [{sp_lo:.3f}x, {sp_hi:.3f}x]")

    gated = sp_lo > args.gate
    print()
    print(f"Gate (lower bound > {args.gate}): {'PASS' if gated else 'FAIL'}")
    print(f"  → speedup claim is "
          f"{'DEFENSIBLE' if gated else 'NOT DEFENSIBLE (CI crosses gate)'}")
    sys.exit(0 if gated else 1)


if __name__ == "__main__":
    main()
