#!/usr/bin/env python3
"""measure_superoptimizer_resistance.py
-----------------------------------------
Empirical ablation: does the variant's slow.c become as fast as fast.c when
compiled with LLVM-ecosystem superoptimizers that go beyond standard -O3?

Regimes (auto-detected; missing tools are skipped with a notice):
  - clang_O3:     clang -O3 -fno-lto                                  (baseline)
  - clang_polly:  clang -O3 -mllvm -polly                             (polyhedral)
                  -mllvm -polly-process-unprofitable -fno-lto
  - clang_souper: sclang -O3 -fno-lto                                 (SMT peephole)

The ablation supports the §Compiler-Resistance Validation claim in
docs/implementation.tex. A pattern survives a regime if the regime's measured
fast/slow speedup remains > 2x — i.e., the superoptimizer did NOT close the
hand-coded gap. The expected per-category outcome (from the published scope
of each tool) is documented in docs/related_work.tex §Superoptimization.

Output: dataset/measured_superopt_resistance.csv
Columns: variant_id, pattern_id, category, difficulty,
         speedup_<regime> for each detected regime,
         min_speedup_across_regimes, resistant (bool)
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.batch_test import extract_extern_decl  # noqa: E402

_C_HEADERS = (
    "#include <stdio.h>\n#include <stdlib.h>\n"
    "#include <math.h>\n#include <string.h>\n\n"
)


def detect_tools() -> dict:
    """Return {regime_name: (compiler_binary, list_of_extra_flags)} for
    available tools. Missing tools are silently omitted."""
    regimes: dict = {}
    if shutil.which("clang"):
        regimes["clang_O3"] = ("clang", ["-O3", "-fno-lto"])
        # Probe Polly support: try to compile a trivial program with it.
        with tempfile.NamedTemporaryFile(suffix=".c", mode="w",
                                          delete=False) as f:
            f.write("int main(void) { return 0; }\n")
            probe = f.name
        try:
            r = subprocess.run(
                ["clang", "-O3", "-mllvm", "-polly",
                 "-o", os.devnull, probe],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                regimes["clang_polly"] = (
                    "clang",
                    ["-O3",
                     "-mllvm", "-polly",
                     "-mllvm", "-polly-process-unprofitable",
                     "-fno-lto"],
                )
        except Exception:
            pass
        finally:
            try:
                os.unlink(probe)
            except OSError:
                pass
    if shutil.which("sclang"):
        regimes["clang_souper"] = ("sclang", ["-O3", "-fno-lto"])
    return regimes


def _build_sources(variant_dir: Path, work: Path):
    slow = (variant_dir / "slow.c").read_text()
    fast = (variant_dir / "fast.c").read_text()
    test = (variant_dir / "test.c").read_text()
    helper = variant_dir / "helper.c"

    if "SLOW_CODE_HERE" not in test:
        return None
    test_with_decls = (test
        .replace("// SLOW_CODE_HERE", extract_extern_decl(slow))
        .replace("// FAST_CODE_HERE", extract_extern_decl(fast)))

    (work / "slow.c").write_text(
        (_C_HEADERS if "#include" not in slow else "") + slow)
    (work / "fast.c").write_text(
        (_C_HEADERS if "#include" not in fast else "") + fast)
    (work / "test.c").write_text(test_with_decls)
    sources = [str(work / "test.c"), str(work / "slow.c"), str(work / "fast.c")]
    if helper.exists():
        sources.append(str(helper))
    return sources


def compile_and_time(variant_dir: str, regime_name: str,
                     compiler: str, flags: list, timeout: int = 60) -> dict:
    """Compile slow + fast + test (+helper.c) as separate TUs under the regime;
    run once; return {compiles, correct, slow_ms, fast_ms, speedup, error}."""
    variant = Path(variant_dir)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        sources = _build_sources(variant, tmp)
        if not sources:
            return {"compiles": False, "error": "no SLOW_CODE_HERE marker"}
        bin_path = tmp / f"bench_{regime_name}"
        try:
            r = subprocess.run(
                [compiler, *flags, "-o", str(bin_path), *sources, "-lm"],
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"compiles": False, "error": "compile-timeout"}
        if r.returncode != 0:
            return {"compiles": False, "error": r.stderr[:300]}

        try:
            r = subprocess.run([str(bin_path)], capture_output=True,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"compiles": True, "correct": False, "error": "run-timeout"}
        if r.returncode != 0:
            return {"compiles": True, "correct": False,
                    "error": r.stderr[:200]}

        parts = dict(p.split("=") for p in r.stdout.strip().split()
                     if "=" in p)
        return {
            "compiles": True,
            "correct":  parts.get("correct", "0") == "1",
            "slow_ms":  float(parts.get("slow_ms", 0)),
            "fast_ms":  float(parts.get("fast_ms", 0)),
            "speedup":  float(parts.get("speedup", 0)),
        }


def _pattern_threshold(meta: dict) -> float:
    """Return the per-pattern resistance threshold.

    Threshold = min(2.0, lower_bound_of_expected_speedup_range). Mirrors
    scripts/measure_compiler_fixable.py::_pattern_threshold so the two
    scripts apply the SAME bar to the SAME variant. Without this, HR-2
    (expected lower 1.5x) and IS-2 (expected lower 1.1x) get flagged as
    "Polly closed the gap" by this script even when their measured
    speedup is still above their authorial floor — disagreeing with the
    compiler-fixable script's verdict on the same data.
    """
    rng = meta.get("expected_speedup_range")
    if not rng:
        return 2.0
    try:
        low_str = str(rng).split("-")[0].strip().rstrip("xX")
        return min(2.0, float(low_str))
    except (ValueError, IndexError):
        return 2.0


def measure_one(args) -> dict:
    """Top-level callable for multiprocessing (must be picklable)."""
    variant_dir, regimes = args
    meta = json.loads((Path(variant_dir) / "metadata.json").read_text())
    threshold = _pattern_threshold(meta)
    row = {
        "variant_id": meta["variant_id"],
        "pattern_id": meta["pattern_id"],
        "category":   meta["category"],
        "difficulty": meta["difficulty"],
        "resistance_threshold": threshold,
    }
    for regime, (compiler, flags) in regimes.items():
        r = compile_and_time(variant_dir, regime, compiler, flags)
        if r.get("compiles") and r.get("correct"):
            row[f"speedup_{regime}"] = r["speedup"]
        else:
            row[f"speedup_{regime}"] = None
    speedups = [v for k, v in row.items()
                if k.startswith("speedup_") and v is not None]
    if speedups:
        row["min_speedup_across_regimes"] = min(speedups)
        # 5% noise margin (matches measure_compiler_fixable.py's tolerance)
        # so a variant doesn't flap resistant/non-resistant across runs
        # purely from parallel-worker contention.
        row["resistant"] = min(speedups) >= threshold * 0.95
    else:
        row["min_speedup_across_regimes"] = None
        row["resistant"] = None
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset_dir", nargs="?", default="dataset")
    parser.add_argument("--out",
                        default="dataset/measured_superopt_resistance.csv")
    parser.add_argument("--workers", type=int,
                        default=min(8, (os.cpu_count() or 4)))
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N variants (smoke testing)")
    args = parser.parse_args()

    regimes = detect_tools()
    if not regimes:
        print("ERROR: no supported tools found. Need at least `clang` for "
              "baseline; optionally Polly (built into clang) and/or `sclang` "
              "(the Souper drop-in wrapper from google/souper).",
              file=sys.stderr)
        sys.exit(2)

    print("Detected superoptimizer regimes:")
    for r, (c, f) in regimes.items():
        print(f"  {r:14s}  {c} {' '.join(f)}")
    print()

    variants = []
    for root, _, files in os.walk(args.dataset_dir):
        if "metadata.json" in files and "slow.c" in files:
            variants.append(root)
    variants.sort()
    if args.limit:
        variants = variants[:args.limit]
    print(f"Sweeping {len(variants)} variants × {len(regimes)} regimes "
          f"({args.workers} workers)...\n")

    rows = []
    work = [(v, regimes) for v in variants]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(measure_one, w): w[0] for w in work}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                rows.append(fut.result())
                if i % 25 == 0 or i == len(variants):
                    print(f"  [{i}/{len(variants)}]")
            except Exception as e:
                print(f"  variant {futures[fut]} failed: {e}",
                      file=sys.stderr)

    if not rows:
        print("No results.", file=sys.stderr)
        sys.exit(1)

    fieldnames = ["variant_id", "pattern_id", "category", "difficulty",
                  "resistance_threshold"]
    for regime in regimes:
        fieldnames.append(f"speedup_{regime}")
    fieldnames += ["min_speedup_across_regimes", "resistant"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {len(rows)} rows → {args.out}\n")

    by_pattern: dict = {}
    for r in rows:
        by_pattern.setdefault(r["pattern_id"], []).append(r)
    hdr = f"{'Pattern':<10} {'N':>4} {'Resistant':>10}  "
    hdr += "  ".join(f"avg_{r}" for r in regimes)
    print(hdr)
    print("-" * (len(hdr) + 5))
    for pid in sorted(by_pattern.keys()):
        rs = by_pattern[pid]
        n = len(rs)
        n_resistant = sum(1 for r in rs if r.get("resistant"))
        parts = []
        for regime in regimes:
            spds = [r[f"speedup_{regime}"] for r in rs
                    if r.get(f"speedup_{regime}")]
            avg = (sum(spds) / len(spds)) if spds else 0.0
            parts.append(f"{avg:>6.1f}x")
        print(f"{pid:<10} {n:>4} {n_resistant:>5}/{n:<4}  " + " ".join(parts))


if __name__ == "__main__":
    main()
