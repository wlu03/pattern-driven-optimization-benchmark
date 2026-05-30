#!/usr/bin/env python3
"""setup_randomization_all.py — Mytkowicz-style setup sweep over all patterns.

For each base pattern in PATTERNS, runs setup_randomization.sh to produce
16 measurements varying link order x env padding (4x4), then bootstraps
a 95% confidence interval on the speedup ratio.

Per the §Statistical Methodology section of docs/implementation.tex, a
speedup claim is gated on the lower CI bound exceeding 1.0 — patterns
whose CI crosses 1.0 are reclassified as 'no measurable speedup' rather
than published as point estimates that fall to measurement bias.

Outputs (under --out):
  per_pattern/<PID>/setup_runs.csv     (16 rows each, raw measurements)
  summary.csv                          (one row per pattern with CI)
  summary.txt                          (human-readable table for paper)

Reference:
  Mytkowicz, Diwan, Hauswirth, Sweeney. "Producing Wrong Data Without
  Doing Anything Obviously Wrong!" ASPLOS 2009.
"""
import argparse
import csv
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdob_core.patterns import PATTERNS  # noqa: E402
from scripts.bootstrap_speedup_ci import (  # noqa: E402
    read_timings, median, bootstrap_speedup_ci,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_one(args) -> dict:
    pattern_id, out_root = args
    pattern_dir = out_root / "per_pattern" / pattern_id
    pattern_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    r = subprocess.run(
        ["bash",
         str(REPO_ROOT / "scripts" / "setup_randomization.sh"),
         pattern_id, str(pattern_dir)],
        capture_output=True, text=True, timeout=900,
    )
    elapsed = time.time() - t0

    csv_path = pattern_dir / "setup_runs.csv"
    if not csv_path.exists():
        return {
            "pattern_id": pattern_id,
            "status":     "failed",
            "error":      (r.stderr or r.stdout)[:200],
            "elapsed_s":  elapsed,
        }

    slow = read_timings(str(csv_path), "slow_ms")
    fast = read_timings(str(csv_path), "fast_ms")
    if len(slow) < 2 or len(fast) < 2:
        return {
            "pattern_id": pattern_id,
            "status":     "insufficient",
            "n_setups":   len(slow),
            "elapsed_s":  elapsed,
        }

    try:
        sp_med, sp_lo, sp_hi = bootstrap_speedup_ci(slow, fast, resamples=10_000)
    except Exception as e:
        return {
            "pattern_id": pattern_id, "status": "ci-failed",
            "error": str(e)[:200], "elapsed_s": elapsed,
        }

    return {
        "pattern_id":      pattern_id,
        "status":          "ok",
        "n_setups":        len(slow),
        "slow_median_ms":  median(slow),
        "fast_median_ms":  median(fast),
        "speedup_median":  sp_med,
        "speedup_ci_lo":   sp_lo,
        "speedup_ci_hi":   sp_hi,
        "spread_pct":      100.0 * (sp_hi - sp_lo) / sp_med if sp_med else 0,
        "defensible":      sp_lo > 1.0,
        "elapsed_s":       elapsed,
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="setup_randomization_results")
    parser.add_argument("--workers", type=int,
                        default=min(4, (os.cpu_count() or 2)),
                        help="Parallel patterns; each spawns 16 internal compiles")
    parser.add_argument("--patterns", default=None,
                        help="Comma-separated pattern IDs (default: all)")
    args = parser.parse_args()

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if args.patterns:
        wanted = {x.strip() for x in args.patterns.split(",")}
        ids = [p.pattern_id for p in PATTERNS if p.pattern_id in wanted]
    else:
        ids = [p.pattern_id for p in PATTERNS if p.test_harness.strip()]

    print(f"Setup randomization sweep over {len(ids)} pattern(s)  "
          f"({args.workers} parallel)")
    print(f"Output dir: {out_root}\n")

    rows = []
    t_start = time.time()
    work = [(pid, out_root) for pid in ids]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, w): w[0] for w in work}
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                row = fut.result()
            except Exception as e:
                row = {"pattern_id": pid, "status": "worker-error",
                       "error": str(e)[:200]}
            rows.append(row)
            if row.get("status") == "ok":
                flag = "PASS" if row["defensible"] else "WEAK"
                print(f"  [{flag}] {pid:<8}  n={row['n_setups']:>2}  "
                      f"median={row['speedup_median']:>10.2f}x  "
                      f"CI=[{row['speedup_ci_lo']:>10.2f}x, "
                      f"{row['speedup_ci_hi']:>10.2f}x]  "
                      f"spread={row['spread_pct']:>5.1f}%  "
                      f"({row['elapsed_s']:.0f}s)")
            else:
                print(f"  [{row.get('status'):>4}] {pid:<8}  "
                      f"{row.get('error', '')[:80]}  "
                      f"({row.get('elapsed_s', 0):.0f}s)")

    rows.sort(key=lambda r: r["pattern_id"])

    fieldnames = ["pattern_id", "status", "n_setups",
                  "slow_median_ms", "fast_median_ms",
                  "speedup_median", "speedup_ci_lo", "speedup_ci_hi",
                  "spread_pct", "defensible", "elapsed_s", "error"]
    summary_csv = out_root / "summary.csv"
    with open(summary_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    ok = [r for r in rows if r.get("status") == "ok"]
    defensible = [r for r in ok if r["defensible"]]
    weak = [r for r in ok if not r["defensible"]]
    failed = [r for r in rows if r.get("status") not in ("ok",)]

    out_lines = []
    out_lines.append(f"Setup-randomization sweep — {len(rows)} patterns, "
                     f"wall-clock {time.time() - t_start:.0f}s")
    out_lines.append(f"  Defensible (CI lower > 1.0): {len(defensible)}")
    out_lines.append(f"  Weak (CI crosses 1.0):       {len(weak)}")
    out_lines.append(f"  Failed:                      {len(failed)}")
    out_lines.append("")
    if defensible:
        out_lines.append("=== Defensible patterns (sorted by CI lower bound) ===")
        out_lines.append(f"  {'pat':<8} {'n':>2}  {'median':>11}  {'CI low':>11}  "
                         f"{'CI high':>11}  spread%")
        for r in sorted(defensible, key=lambda r: -r["speedup_ci_lo"]):
            out_lines.append(
                f"  {r['pattern_id']:<8} {r['n_setups']:>2}  "
                f"{r['speedup_median']:>9.2f}x  "
                f"{r['speedup_ci_lo']:>9.2f}x  "
                f"{r['speedup_ci_hi']:>9.2f}x  "
                f"{r['spread_pct']:>5.1f}%")
    if weak:
        out_lines.append("")
        out_lines.append("=== Weak / unsupported patterns (single-setup claim unsafe) ===")
        for r in sorted(weak, key=lambda r: r["speedup_median"]):
            out_lines.append(
                f"  {r['pattern_id']:<8} {r['n_setups']:>2}  "
                f"median={r['speedup_median']:.2f}x  "
                f"CI=[{r['speedup_ci_lo']:.2f}, {r['speedup_ci_hi']:.2f}]")
    if failed:
        out_lines.append("")
        out_lines.append("=== Failed to measure ===")
        for r in failed:
            out_lines.append(f"  {r['pattern_id']:<8} {r.get('status'):<12}  "
                             f"{r.get('error', '')[:80]}")

    summary_txt = out_root / "summary.txt"
    summary_txt.write_text("\n".join(out_lines) + "\n")
    print()
    print("\n".join(out_lines))
    print()
    print(f"Wrote {summary_csv}")
    print(f"Wrote {summary_txt}")


if __name__ == "__main__":
    main()
