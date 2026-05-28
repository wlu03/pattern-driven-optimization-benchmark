#!/usr/bin/env python3
"""
Multi-input benchmark runner.

Compiles ONE pattern's harness (using fast_code from patterns.py by default,
or a user-supplied C file containing an `optimized` function) and executes
it under multiple (n, seed, distribution) configurations, exposing the
input-sensitivity that the single-fixed-input harness hides.

Why this exists
---------------
The original PatternEntry.test_harness bakes in a single set of inputs
(`n = 1000000; srand(42);`).  That makes it trivial for an LLM to
special-case the constants it sees in the prompt — and worse, it makes the
"input-sensitive" (IS-*) category completely unobservable because every IS
pattern is timed against one fixed distribution.  This runner uses the
multi-input env-var hooks injected by patterns.py to re-run the same
compiled harness under different inputs.

CLI
---
    python3 scripts/run_multi_input.py --pattern SR-1
    python3 scripts/run_multi_input.py --pattern IS-4 --configs cfg.json
    python3 scripts/run_multi_input.py --pattern SR-1 --code-source slow

`configs.json` is a JSON array of objects, each with optional keys:
    n     — integer, sets BENCH_N (default: harness default)
    seed  — integer, sets BENCH_SEED
    dist  — one of: random, sorted, reverse_sorted, all_zero, sparse
            (only IS-* patterns react to this; others ignore it)
    label — optional human-readable name for the config

When --configs is omitted, a sensible default sweep is run:
    3 sizes (small/medium/large from a per-pattern table)
  × 3 seeds (42, 123, 7919)
  × distributions applicable to the pattern (all 5 for IS-* and IS-5,
    just "random" for the rest — they don't react to dist anyway).

Output
------
A summary table to stdout: per-config median time + per-config correctness,
plus an aggregate "worst-case" speedup (minimum speedup across configs)
relative to the slow_code on the same config.  Any failed correctness
check is loudly flagged — the run is considered FAILED if ANY config
produced an incorrect result.
"""
import argparse
import json
import os
import statistics
import sys
from pathlib import Path

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdob_core.compiler import compile_and_run, normalize_function_name  # noqa: E402
from pdob_core.patterns import PATTERNS  # noqa: E402


# Patterns that consume BENCH_DIST in their fill code.  Other patterns will
# silently ignore the env var but we don't bother sweeping over distribution
# for them since it produces redundant configurations.
DIST_AWARE = {"IS-1", "IS-2", "IS-3", "IS-4", "IS-5"}
ALL_DISTS = ["random", "sorted", "reverse_sorted", "all_zero", "sparse"]

# Default size sweep — `n` is overridden via BENCH_N.  These values are
# chosen to be 10x-spaced where possible while staying within reasonable
# wall-clock budgets across all patterns.  Patterns whose harness ignores
# BENCH_N (e.g. AL-1/AL-4 which use a fixed small int) just see one size.
DEFAULT_SIZES = [100000, 1000000, 5000000]
DEFAULT_SEEDS = [42, 123, 7919]


def default_configs(pattern_id: str):
    """Build the default sweep for a pattern: sizes × seeds × distributions."""
    dists = ALL_DISTS if pattern_id in DIST_AWARE else ["random"]
    cfgs = []
    for n in DEFAULT_SIZES:
        for seed in DEFAULT_SEEDS:
            for dist in dists:
                cfgs.append({
                    "n": n, "seed": seed, "dist": dist,
                    "label": f"n={n} seed={seed} dist={dist}",
                })
    return cfgs


def env_for(cfg: dict) -> dict:
    """Build a subprocess env dict from a config (passed through to the binary)."""
    env = dict(os.environ)
    if cfg.get("n") is not None:
        env["BENCH_N"] = str(cfg["n"])
    if cfg.get("seed") is not None:
        env["BENCH_SEED"] = str(cfg["seed"])
    if cfg.get("dist"):
        env["BENCH_DIST"] = str(cfg["dist"])
    return env


def load_code(pattern, source: str) -> str:
    """Resolve `--code-source` into the C code to bench under `// LLM_CODE_HERE`."""
    if source in ("fast", "patterns.py"):
        return normalize_function_name(pattern.fast_code)
    if source == "slow":
        return normalize_function_name(pattern.slow_code)
    # otherwise: treat as a path to a .c file
    path = Path(source)
    if not path.exists():
        raise SystemExit(f"--code-source: {source!r} is neither 'fast'/'slow'/'patterns.py' nor a real file path")
    return normalize_function_name(path.read_text())


def run_one(code: str, harness: str, cfg: dict, runs: int, timeout: int) -> dict:
    """Invoke the compiled harness once under the given config; returns timing/correctness."""
    return compile_and_run(code, harness, runs=runs, timeout=timeout, env=env_for(cfg))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else "")
    ap.add_argument("--pattern", required=True, help="Pattern ID, e.g. SR-1, IS-4")
    ap.add_argument("--configs", help="Path to a JSON file listing configs (see module docstring)")
    ap.add_argument("--code-source", default="fast",
                    help="'fast' (default) | 'slow' | 'patterns.py' (alias for fast) | path to .c file")
    ap.add_argument("--runs", type=int, default=3, help="Median over this many runs per config")
    ap.add_argument("--timeout", type=int, default=180, help="Per-run timeout (seconds)")
    ap.add_argument("--no-compare-slow", action="store_true",
                    help="Skip slow_code baseline (no speedup column — useful when you only want fast timing)")
    args = ap.parse_args(argv)

    pattern = next((p for p in PATTERNS if p.pattern_id == args.pattern), None)
    if pattern is None:
        raise SystemExit(f"Unknown pattern: {args.pattern}. Known: {[p.pattern_id for p in PATTERNS]}")

    if args.configs:
        configs = json.loads(Path(args.configs).read_text())
        # Inject default labels if missing
        for i, c in enumerate(configs):
            c.setdefault("label", f"cfg[{i}] n={c.get('n','-')} seed={c.get('seed','-')} dist={c.get('dist','random')}")
    else:
        configs = default_configs(args.pattern)

    code = load_code(pattern, args.code_source)
    slow_code = normalize_function_name(pattern.slow_code) if not args.no_compare_slow else None

    print(f"Pattern: {pattern.pattern_id} — {pattern.name}")
    print(f"Code source: {args.code_source}")
    print(f"Configs: {len(configs)}\n")
    header = f"{'CONFIG':<48} {'fast_ms':>10} {'slow_ms':>10} {'speedup':>10} {'correct':>8}"
    print(header)
    print("-" * len(header))

    results = []
    any_incorrect = False
    speedups = []

    for cfg in configs:
        rf = run_one(code, pattern.test_harness, cfg, args.runs, args.timeout)
        if not rf.get("compiles"):
            print(f"{cfg['label']:<48} COMPILE FAIL: {(rf.get('error') or '')[:200]}")
            any_incorrect = True
            results.append({"cfg": cfg, "fast": rf, "slow": None})
            continue
        if not rf.get("correct"):
            any_incorrect = True

        slow_ms = "-"
        speedup = "-"
        rs = None
        if slow_code is not None:
            rs = run_one(slow_code, pattern.test_harness, cfg, args.runs, args.timeout)
            if rs.get("compiles") and rs.get("correct"):
                slow_ms_v = rs["time_ms"]
                sp = slow_ms_v / max(rf["time_ms"], 1e-6)
                speedup = f"{sp:.2f}x"
                slow_ms = f"{slow_ms_v:.2f}"
                speedups.append(sp)
            else:
                slow_ms = "FAIL"

        print(f"{cfg['label']:<48} {rf['time_ms']:>10.2f} {slow_ms:>10} {speedup:>10} {('OK' if rf['correct'] else 'BAD'):>8}")
        results.append({"cfg": cfg, "fast": rf, "slow": rs})

    print()
    if speedups:
        print(f"Worst-case speedup: {min(speedups):.2f}x")
        print(f"Median speedup    : {statistics.median(speedups):.2f}x")
        print(f"Best-case speedup : {max(speedups):.2f}x")
    print(f"Overall: {'FAILED — at least one config produced an incorrect result' if any_incorrect else 'OK (all configs correct)'}")
    return 1 if any_incorrect else 0


if __name__ == "__main__":
    sys.exit(main())
