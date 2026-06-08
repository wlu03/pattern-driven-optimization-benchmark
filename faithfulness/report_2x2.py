"""
report_2x2.py
-------------
Cross-tabulate LLM speedup against structural faithfulness, producing two
publication-relevant analyses:

  Report 1 — faithful x fast 2x2 matrix (per pattern, per model, overall)
  Report 2 — pycparser parse-success rate per pattern

Usage:
    python3 faithfulness/report_2x2.py [results.csv] \
        [--faithfulness <path>] [--out <dir>] \
        [--fast-threshold 1.5] [--suspicious-ratio 10.0]

If --faithfulness is omitted (or the file does not exist), this script computes
faithfulness on the fly from the `llm_code` column of the results CSV by
invoking faithfulness/checkers.py directly (no subprocess, no external deps
beyond pycparser which is already required).

Output:
    Stdout                        : pretty-printed tables
    <out>/faithful_fast_2x2.csv   : machine-readable per-pattern breakdown
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

# Allow running from faithfulness/ or from repo root.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))                  # for `checkers`
sys.path.insert(0, str(_HERE.parent))           # for `pdob_core`

import checkers as _checkers_mod                # type: ignore
from checkers import (                          # type: ignore
    CHECKERS,
    Verdict,
    check_faithfulness,
    PatternChecker,
)
# `_parse` lives in the helpers submodule; the per-checker helpers
# (`_calls_at_depth`, `_loop_stats`, …) resolve it through *that* module's
# globals, so we must monkey-patch it there for instrumentation to take
# effect. The package re-exports `_parse` from `__init__` for backward
# compatibility, but patching `_checkers_mod._parse` alone is not enough.
from checkers import _ast_helpers as _ast_helpers_mod  # type: ignore

# `pdob_core.patterns` is optional — only needed for on-the-fly faithfulness
# when the results CSV doesn't ship a `slow_code` column.
try:
    from pdob_core.patterns import PATTERNS    # type: ignore
    _PATTERNS_BY_ID = {p.pattern_id: p for p in PATTERNS}
except Exception:
    _PATTERNS_BY_ID = {}

# COMP variants carry their constituent pattern list in dataset metadata. The
# COMP checker NEEDS that list: without it, it falls back to a generic regex
# battery that massively over-reports `FAITHFUL` (COMP is ~54% of the dataset,
# so this dominates the aggregate). Build variant_id -> composition lazily so
# non-COMP runs pay nothing, and resolve the dataset relative to the repo root
# so the lookup works regardless of the caller's cwd.
_COMP_COMPOSITION: Optional[dict] = None


def _composition_for(variant_id: str):
    global _COMP_COMPOSITION
    if _COMP_COMPOSITION is None:
        _COMP_COMPOSITION = {}
        try:
            from pdob_core.dataset_evaluator import discover_variants  # type: ignore
            for v in discover_variants(str(_HERE.parent / "dataset")):
                comp = v.metadata.get("composition") if getattr(v, "metadata", None) else None
                if comp:
                    _COMP_COMPOSITION[v.variant_id] = comp
        except Exception:
            pass
    return _COMP_COMPOSITION.get(variant_id)


# --------------------------------------------------------------------------
# Instrumentation: wrap PatternChecker.check + _parse so we can report
# whether each faithfulness verdict came from the AST path or the regex
# fallback, and how often pycparser actually succeeded.
# --------------------------------------------------------------------------

class _Instrumentation:
    """Per-(pattern, run) record of which code path the checker took."""

    def __init__(self) -> None:
        # Counters accumulated for the current `check_faithfulness` call.
        self.parse_attempts = 0
        self.parse_failures = 0
        # The "path" taken by the most recent call:
        #   "ast"      — _ast_check returned a non-UNKNOWN verdict
        #   "regex"    — fell back to _regex_check (with or without parse failure)
        #   "no_ast"   — checker has no _ast_check override at all
        self.last_path: Optional[str] = None
        self.last_parse_failed: bool = False

    def reset(self) -> None:
        self.parse_attempts = 0
        self.parse_failures = 0
        self.last_path = None
        self.last_parse_failed = False


_INSTR = _Instrumentation()


def _install_instrumentation() -> None:
    """Monkey-patch _parse + PatternChecker.check to track path-taken.

    We do NOT modify the checkers package — everything is done in this
    script. `_parse` is patched in the `_ast_helpers` submodule because
    that is where the per-checker helpers (`_calls_at_depth`, `_loop_stats`,
    …) resolve the symbol from. We mirror the patch onto the package itself
    so any external consumer of `checkers._parse` also picks it up."""

    orig_parse = _ast_helpers_mod._parse

    def instrumented_parse(code: str):
        _INSTR.parse_attempts += 1
        result = orig_parse(code)
        if result is None:
            _INSTR.parse_failures += 1
            _INSTR.last_parse_failed = True
        return result

    _ast_helpers_mod._parse = instrumented_parse
    _checkers_mod._parse = instrumented_parse

    # Replace helpers that hold a direct reference to the original _parse.
    # Re-binding the symbol in `_ast_helpers` is enough: `_calls_at_depth`,
    # `_loop_stats`, etc. were defined *using* the bare name `_parse`, so
    # Python resolves it at call time via the helpers module's globals and
    # the monkey-patch is picked up automatically. We verify this in the
    # smoke test below.

    orig_check = PatternChecker.check

    def instrumented_check(self, slow_code: str, model_output: str):
        # Detect whether this checker has an _ast_check override.
        has_ast = type(self)._ast_check is not PatternChecker._ast_check

        if not has_ast:
            _INSTR.last_path = "no_ast"
            return self._regex_check(slow_code, model_output)

        ast_result = self._ast_check(slow_code, model_output)
        if ast_result is not None and ast_result.verdict != Verdict.UNKNOWN:
            _INSTR.last_path = "ast"
            return ast_result

        _INSTR.last_path = "regex"
        return self._regex_check(slow_code, model_output)

    PatternChecker.check = instrumented_check  # type: ignore[assignment]


_install_instrumentation()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _to_float(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _to_bool(x) -> bool:
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    s = str(x).strip().lower()
    return s in ("true", "1", "yes", "y", "t")


def _read_results_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    rows: list[dict] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _read_faithfulness_file(path: str) -> dict[tuple[str, str, str], str]:
    """Read previously computed faithfulness results.

    Returns a dict keyed by (model, strategy, pattern_id) -> verdict.

    If model/strategy are absent (the evaluate_faithfulness.py CSV does not
    carry them), the key collapses to ('', '', pattern_id). Callers should
    treat that as a per-pattern fallback.
    """
    out: dict[tuple[str, str, str], str] = {}
    if not path or not os.path.exists(path):
        return out

    if path.endswith(".json") or path.endswith(".jsonl"):
        with open(path) as f:
            if path.endswith(".jsonl"):
                items = [json.loads(line) for line in f if line.strip()]
            else:
                items = json.load(f)
                if isinstance(items, dict):
                    items = items.get("results", [])
    else:
        # CSV
        with open(path, newline="") as f:
            items = list(csv.DictReader(f))

    for it in items:
        pid = it.get("pattern_id", "")
        model = it.get("model", "")
        strategy = it.get("strategy", "")
        verdict = it.get("verdict", "")
        key = (model, strategy, pid)
        out[key] = verdict
    return out


def _compute_faithfulness_for_row(
    row: dict,
) -> tuple[str, Optional[str]]:
    """Run the checker on a single results row. Returns (verdict, path_taken).

    path_taken is one of "ast", "regex", "no_ast", or None if the checker
    could not run (e.g. missing pattern).
    """
    pid = row.get("pattern_id", "")
    llm_code = row.get("llm_code", "") or ""
    if not pid or pid not in CHECKERS:
        return (Verdict.UNKNOWN, None)

    pattern = _PATTERNS_BY_ID.get(pid)
    slow_code = pattern.slow_code if pattern is not None else ""

    _INSTR.reset()
    try:
        if pid == "COMP":
            # Thread the composition so COMPChecker scores the actual
            # constituent transforms instead of the over-reporting regex
            # fallback. Mirrors scripts/rescore_faithfulness.py.
            result = check_faithfulness(
                pid, slow_code, llm_code,
                composition=_composition_for(row.get("variant_id", "")),
            )
        else:
            result = check_faithfulness(pid, slow_code, llm_code)
    except Exception:
        return (Verdict.UNKNOWN, _INSTR.last_path)
    return (result.verdict, _INSTR.last_path)


# --------------------------------------------------------------------------
# 2x2 classification
# --------------------------------------------------------------------------

# Two-axis faithfulness cells (the `faithfulness_cell` column): the canonical
# cascade categories (equivalence x expected-shape). The headline report breaks
# each down by fast/slow rather than collapsing to a binary faithful column, so
# FAITHFUL_ALTERNATIVE (equivalent via a different transform) is no longer
# conflated with the genuine failures.
FAITHFUL    = "FAITHFUL"               # expected transform AND equivalent
FAITH_ALT   = "FAITHFUL_ALTERNATIVE"   # equivalent via a different transform
STRUCT_ONLY = "STRUCTURAL_ONLY"        # expected shape but NOT equivalent
FAILED      = "FAILED"                 # neither
CELLS = [FAITHFUL, FAITH_ALT, STRUCT_ONLY, FAILED]
CELL_HDR = {FAITHFUL: "FAITHFUL", FAITH_ALT: "FAITH_ALT",
            STRUCT_ONLY: "STRUCT_ONLY", FAILED: "FAILED"}


def _synth_cell(verdict: str, equivalent: bool) -> str:
    """Route a single-axis structural verdict + an equivalence bit into a
    two-axis cell. Used only when the canonical `faithfulness_cell` column is
    absent (a raw results CSV, or a --faithfulness override file)."""
    shape = verdict == Verdict.FAITHFUL
    if equivalent and shape:        return FAITHFUL
    if equivalent and not shape:    return FAITH_ALT
    if not equivalent and shape:    return STRUCT_ONLY
    return FAILED


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def _pad(s: str, w: int, right: bool = False) -> str:
    s = str(s)
    if len(s) >= w:
        return s[:w]
    return (s.rjust(w) if right else s.ljust(w))


def _print_cell_table(title: str, counts: dict) -> None:
    """Print fast/slow x four-cell breakdown. `counts` is keyed by
    (speed, cell) with speed in {"fast","slow"} and cell in CELLS."""
    total = sum(counts.values())
    if total == 0:
        return

    def pct(n: int) -> str:
        return f"{n} ({100*n/total:.1f}%)"

    w = 18
    print(f"\n{title}  (n={total})")
    print("  " + f"{'':<6}" + "".join(f"{CELL_HDR[c]:>{w}}" for c in CELLS)
          + f"{'Row':>{w}}")
    for speed in ("fast", "slow"):
        rowsum = sum(counts.get((speed, c), 0) for c in CELLS)
        body = "".join(f"{pct(counts.get((speed, c), 0)):>{w}}" for c in CELLS)
        print(f"  {speed.capitalize():<6}{body}{pct(rowsum):>{w}}")
    colbody = "".join(
        f"{pct(sum(counts.get((s, c), 0) for s in ('fast', 'slow'))):>{w}}"
        for c in CELLS)
    print(f"  {'Col':<6}{colbody}{pct(total):>{w}}")


def _print_per_pattern_table(
    per_pattern: dict[str, dict[str, int]],
    parse_paths: dict[str, dict[str, int]],
) -> None:
    if not per_pattern:
        return
    print("\nPer-pattern four-cell breakdown + parse rate "
          "(FTHFL=FAITHFUL, ALT=FAITHFUL_ALTERNATIVE, STRUCT=STRUCTURAL_ONLY):")
    hdr = (
        f"  {'pattern':<8} {'N':>5} "
        f"{'FTHFL':>7} {'ALT':>7} {'STRUCT':>7} {'FAIL':>7} "
        f"{'parse%':>8} {'ast':>5} {'regex':>5} {'no_ast':>6}"
    )
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for pid in sorted(per_pattern):
        c = per_pattern[pid]
        total = sum(c.values())
        tc = {cell: sum(c.get((s, cell), 0) for s in ("fast", "slow")) for cell in CELLS}
        paths = parse_paths.get(pid, {})
        parse_attempts = paths.get("parse_attempts", 0)
        parse_failures = paths.get("parse_failures", 0)
        parse_succ = parse_attempts - parse_failures
        parse_pct = (100 * parse_succ / parse_attempts) if parse_attempts else 0.0
        print(
            f"  {pid:<8} {total:>5} "
            f"{tc[FAITHFUL]:>7} {tc[FAITH_ALT]:>7} {tc[STRUCT_ONLY]:>7} {tc[FAILED]:>7} "
            f"{parse_pct:>7.1f}% "
            f"{paths.get('ast', 0):>5} {paths.get('regex', 0):>5} "
            f"{paths.get('no_ast', 0):>6}"
        )


def _print_parse_summary(parse_paths: dict[str, dict[str, int]]) -> None:
    print("\nReport 2 — pycparser parse-success rate:")
    if not parse_paths:
        print("  (skipped — every row had a precomputed faithfulness verdict, "
              "so checkers.py was never invoked)")
        return

    print(
        f"  {'pattern':<8} {'checks':>7} {'parse_calls':>12} "
        f"{'succ':>5} {'fail':>5} {'succ%':>7} "
        f"{'ast':>5} {'regex':>5} {'no_ast':>6}"
    )
    print("  " + "-" * 70)

    tot_attempts = tot_failures = tot_checks = 0
    tot_ast = tot_regex = tot_no_ast = 0
    for pid in sorted(parse_paths):
        p = parse_paths[pid]
        attempts = p.get("parse_attempts", 0)
        failures = p.get("parse_failures", 0)
        succ = attempts - failures
        checks = p.get("ast", 0) + p.get("regex", 0) + p.get("no_ast", 0)
        succ_pct = (100 * succ / attempts) if attempts else 0.0
        print(
            f"  {pid:<8} {checks:>7} {attempts:>12} "
            f"{succ:>5} {failures:>5} {succ_pct:>6.1f}% "
            f"{p.get('ast', 0):>5} {p.get('regex', 0):>5} {p.get('no_ast', 0):>6}"
        )
        tot_attempts += attempts
        tot_failures += failures
        tot_checks += checks
        tot_ast += p.get("ast", 0)
        tot_regex += p.get("regex", 0)
        tot_no_ast += p.get("no_ast", 0)

    succ = tot_attempts - tot_failures
    succ_pct = (100 * succ / tot_attempts) if tot_attempts else 0.0
    print("  " + "-" * 70)
    print(
        f"  {'OVERALL':<8} {tot_checks:>7} {tot_attempts:>12} "
        f"{succ:>5} {tot_failures:>5} {succ_pct:>6.1f}% "
        f"{tot_ast:>5} {tot_regex:>5} {tot_no_ast:>6}"
    )
    print(
        "\n  ast    = AST checker delivered the verdict\n"
        "  regex  = checker has AST path but fell back to regex (parse failure or UNKNOWN)\n"
        "  no_ast = checker only implements regex (never tries AST)"
    )


def _print_cell_highlights(
    classifications: list[dict],
    fast_thr: float,
    suspicious_ratio: float,
) -> None:
    """Highlight the two analysis-worthy cells:

    * STRUCTURAL_ONLY — has the expected shape but is NOT equivalent: the code
      looks like the intended transform yet breaks correctness (overfit / DCE /
      hardcoded-output cheats). Flag fast ones whose speedup vs the hand-tuned
      reference is suspiciously high.
    * fast FAITHFUL_ALTERNATIVE — equivalent and fast via a *different* valid
      transform than the labeled one (genuine alternative solutions).
    """
    struct = [r for r in classifications if r["cell"] == STRUCT_ONLY]
    alt_fast = [r for r in classifications
                if r["cell"] == FAITH_ALT and r["fast"]]

    if struct:
        print(f"\nSTRUCTURAL_ONLY (expected shape but not equivalent)  n={len(struct)}:")
        print(
            f"  {'model':<22} {'strategy':<18} {'pattern':<8} "
            f"{'sp_vs_slow':>10} {'sp_vs_ref':>10}  flag"
        )
        for r in sorted(struct, key=lambda x: -x["speedup_vs_slow"])[:40]:
            sp_ref = r["speedup_vs_ref"]
            flag = (f"SUSPICIOUS (>{suspicious_ratio:g}x ref, possible DCE/cheat)"
                    if sp_ref > suspicious_ratio else "")
            print(
                f"  {r['model'][:22]:<22} {r['strategy'][:18]:<18} "
                f"{r['pattern_id']:<8} "
                f"{r['speedup_vs_slow']:>10.2f} {sp_ref:>10.2f}  {flag}"
            )
        if len(struct) > 40:
            print(f"  ... ({len(struct) - 40} more)")

    if alt_fast:
        print(f"\nfast FAITHFUL_ALTERNATIVE (equivalent via a different transform)  "
              f"n={len(alt_fast)}:")
        print(
            f"  {'model':<22} {'strategy':<18} {'pattern':<8} "
            f"{'sp_vs_slow':>10} {'sp_vs_ref':>10}"
        )
        for r in sorted(alt_fast, key=lambda x: -x["speedup_vs_slow"])[:40]:
            print(
                f"  {r['model'][:22]:<22} {r['strategy'][:18]:<18} "
                f"{r['pattern_id']:<8} "
                f"{r['speedup_vs_slow']:>10.2f} {r['speedup_vs_ref']:>10.2f}"
            )
        if len(alt_fast) > 40:
            print(f"  ... ({len(alt_fast) - 40} more)")


# --------------------------------------------------------------------------
# CSV output
# --------------------------------------------------------------------------

def _write_2x2_csv(
    out_dir: str,
    per_model_strategy_pattern: dict[tuple[str, str, str], dict[str, int]],
    parse_paths_per_pattern: dict[str, dict[str, int]],
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "faithful_fast_2x2.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model", "strategy", "pattern_id",
            "faithful", "faithful_alternative", "structural_only", "failed",
            "n_fast", "parse_success_rate",
        ])
        for (model, strategy, pid), counts in sorted(per_model_strategy_pattern.items()):
            p = parse_paths_per_pattern.get(pid, {})
            attempts = p.get("parse_attempts", 0)
            failures = p.get("parse_failures", 0)
            succ_rate = ((attempts - failures) / attempts) if attempts else 0.0
            tc = {cell: sum(counts.get((s, cell), 0) for s in ("fast", "slow"))
                  for cell in CELLS}
            n_fast = sum(counts.get(("fast", cell), 0) for cell in CELLS)
            writer.writerow([
                model, strategy, pid,
                tc[FAITHFUL], tc[FAITH_ALT], tc[STRUCT_ONLY], tc[FAILED],
                n_fast, round(succ_rate, 4),
            ])
    return out_path


# --------------------------------------------------------------------------
# Main driver
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Cross-tabulate LLM speedup against structural faithfulness.")
    parser.add_argument("results_csv", nargs="?", default="results.csv",
                        help="Results CSV from evaluate_llm.py (default: results.csv)")
    parser.add_argument("--faithfulness", default=None,
                        help="Optional CSV/JSON from evaluate_faithfulness.py. "
                             "If omitted or missing, faithfulness is computed "
                             "on the fly from the llm_code column.")
    parser.add_argument("--out", default=".",
                        help="Output directory for CSV (default: .)")
    parser.add_argument("--fast-threshold", type=float, default=1.5,
                        help="speedup_vs_slow > this counts as 'fast' (default: 1.5)")
    parser.add_argument("--suspicious-ratio", type=float, default=10.0,
                        help="Flag STRUCTURAL_ONLY rows whose speedup_vs_ref "
                             "exceeds this (default: 10.0, suggesting DCE/cheat)")
    args = parser.parse_args()

    rows = _read_results_csv(args.results_csv)
    if not rows:
        print(f"no results to report (no rows in {args.results_csv})")
        return 0

    # Faithfulness verdicts — keyed by (model, strategy, pattern_id) when
    # available, else by ('', '', pattern_id) as a fallback.
    precomputed = _read_faithfulness_file(args.faithfulness) if args.faithfulness else {}

    # Counters
    overall_counts: dict[str, int] = defaultdict(int)
    per_pattern_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_model_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_strategy_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_msp_counts: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: defaultdict(int))
    parse_paths_per_pattern: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int))
    classifications: list[dict] = []

    for row in rows:
        pid = row.get("pattern_id", "")
        model = row.get("model", "")
        strategy = row.get("strategy", "")
        compiles = _to_bool(row.get("compiles"))
        correct = _to_bool(row.get("correct"))
        speedup = _to_float(row.get("speedup_vs_slow"))
        speedup_ref = _to_float(row.get("speedup_vs_ref"))

        # Equivalence proxy for the fast/slow axis: an incorrect or
        # non-compiling program has no creditable speedup.
        equivalent_proxy = compiles and correct

        # Two-axis faithfulness cell — source-of-truth precedence:
        #   1. an explicit --faithfulness file (single-axis verdict -> synth),
        #   2. the canonical `faithfulness_cell` column written by
        #      scripts/rescore_faithfulness.py (real slow source + COMP
        #      composition + the full checker registry, computed once),
        #   3. on-the-fly recompute -> synth, ONLY when neither is present
        #      (e.g. a raw results CSV). Only (3) parses per row; recomputing
        #      when the column exists would re-parse every output one-by-one.
        override = precomputed.get((model, strategy, pid)) or precomputed.get(("", "", pid))
        if override is not None:
            cell = _synth_cell(override, equivalent_proxy)
        else:
            col = (row.get("faithfulness_cell") or "").strip().upper()
            if col in CELLS:
                cell = col
            else:
                verdict, path = _compute_faithfulness_for_row(row)
                if path is not None:
                    parse_paths_per_pattern[pid][path] += 1
                    parse_paths_per_pattern[pid]["parse_attempts"] += _INSTR.parse_attempts
                    parse_paths_per_pattern[pid]["parse_failures"] += _INSTR.parse_failures
                cell = _synth_cell(verdict, equivalent_proxy)

        is_fast = equivalent_proxy and speedup > args.fast_threshold
        key = ("fast" if is_fast else "slow", cell)
        overall_counts[key] += 1
        per_pattern_counts[pid][key] += 1
        per_model_counts[model][key] += 1
        per_strategy_counts[strategy][key] += 1
        per_msp_counts[(model, strategy, pid)][key] += 1

        classifications.append({
            "model": model,
            "strategy": strategy,
            "pattern_id": pid,
            "cell": cell,
            "fast": is_fast,
            "speedup_vs_slow": speedup,
            "speedup_vs_ref": speedup_ref,
        })

    # Pre-populate all 8 (speed, cell) buckets so the tables show zeros.
    for d in [overall_counts, *per_pattern_counts.values(),
              *per_model_counts.values(), *per_strategy_counts.values(),
              *per_msp_counts.values()]:
        for speed in ("fast", "slow"):
            for cell in CELLS:
                d.setdefault((speed, cell), 0)

    # ── Report 1 — faithfulness cells x fast/slow ────────────────────────
    print("=" * 72)
    print("Report 1 — faithfulness cells x fast/slow  "
          f"(fast = speedup_vs_slow > {args.fast_threshold:g})")
    print("  FAITHFUL = intended transform + equivalent | "
          "FAITHFUL_ALTERNATIVE = equivalent, different transform")
    print("  STRUCTURAL_ONLY = expected shape, not equivalent | "
          "FAILED = neither")
    print("=" * 72)

    _print_cell_table("OVERALL", overall_counts)

    if len(per_model_counts) > 1 or (per_model_counts and next(iter(per_model_counts)) != ""):
        for model in sorted(per_model_counts):
            _print_cell_table(f"model={model}", per_model_counts[model])
    if len(per_strategy_counts) > 1:
        for strat in sorted(per_strategy_counts):
            _print_cell_table(f"strategy={strat}", per_strategy_counts[strat])

    _print_per_pattern_table(per_pattern_counts, parse_paths_per_pattern)
    _print_cell_highlights(classifications, args.fast_threshold, args.suspicious_ratio)

    # ── Report 2 — Parse rate ────────────────────────────────────────────
    print("\n" + "=" * 72)
    _print_parse_summary(parse_paths_per_pattern)

    # ── CSV output ───────────────────────────────────────────────────────
    out_path = _write_2x2_csv(args.out, per_msp_counts, parse_paths_per_pattern)
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
