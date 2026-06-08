#!/usr/bin/env python3
"""Recompute ONLY the faithfulness columns of an already-scored CSV.

Two faithfulness-only defects motivated this; neither touches timing/
correctness/speedup, so re-running the whole sweep (and churning the validated
speedup/ranking numbers) is unnecessary:

  1. COMP variants were scored by ``COMPChecker`` *without* their composition
     metadata, so it fell back to a generic regex battery that over-reported
     faithful for ~54% of the dataset. The fix (pass ``composition``) lives in
     ``pdob_core.evaluator._compute_faithfulness`` -> ``check_faithfulness``.
  2. The 6 newest cells were scored under an interpreter without pycparser, so
     the AST structural axis was dead (expected_shape False everywhere) and the
     equivalence axis fell back to single-config.

This script re-runs the SAME production faithfulness path per row, reusing the
existing ``llm_code``/``correct`` and rewriting only the seven ``faithfulness_*``
columns. Every other column is passed through byte-for-byte.

Equivalence axis:
  --equivalence reuse      keep the row's existing equivalence columns (correct
                           for the 9 cells scored under base python3); recompute
                           only the structural axis + 2x2 cell. FAST (parse only).
  --equivalence recompute  re-run differential_equivalence_on_variant (needed for
                           the 6 venv-scored cells whose equivalence degraded to
                           single-config). SLOW (compiles+runs per row).

Run under base python3 (has pycparser; matches how the good cells were scored).
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.getcwd())
csv.field_size_limit(sys.maxsize)

from pdob_core.dataset_evaluator import discover_variants  # noqa: E402
from pdob_core.evaluator import _compute_faithfulness  # noqa: E402


def _b(s) -> bool:
    return str(s).strip().lower() in ("true", "1", "yes")


def _route_cell(is_equiv: bool, expected_shape: bool) -> str:
    # Identical routing to pdob_core.evaluator.evaluate_variant.
    if is_equiv and expected_shape:
        return "FAITHFUL"
    if is_equiv and not expected_shape:
        return "FAITHFUL_ALTERNATIVE"
    if (not is_equiv) and expected_shape:
        return "STRUCTURAL_ONLY"
    return "FAILED"


def recompute_row(row: dict, variant, slow_src: str, mode: str) -> dict:
    code = row.get("llm_code", "") or ""
    # Structural axis (fast, AST) — now composition-aware for COMP.
    f = _compute_faithfulness(
        variant.pattern_id, slow_src, code,
        test_harness=None, composition=variant.metadata.get("composition"),
    )
    struct_verdict = f.get("faithfulness_structural_verdict")
    expected_shape = (struct_verdict == "faithful")

    if mode == "recompute":
        try:
            from faithfulness.equivalence import differential_equivalence_on_variant
            eq = differential_equivalence_on_variant(
                code, variant, n_inputs=9, opt_level="O2")
            if eq.n_configs > 0 and not eq.compile_error:
                is_equiv, n_cfg, n_pass = eq.equivalent, eq.n_configs, eq.n_correct
            else:
                is_equiv = _b(row.get("correct")); n_cfg, n_pass = 1, int(is_equiv)
        except Exception:
            is_equiv = _b(row.get("correct")); n_cfg, n_pass = 1, int(is_equiv)
    else:  # reuse the equivalence already in the CSV
        ev = row.get("faithfulness_equivalent", "")
        is_equiv = _b(ev) if ev != "" else _b(row.get("correct"))
        n_cfg = row.get("faithfulness_equiv_configs") or 1
        n_pass = row.get("faithfulness_equiv_passed") or int(is_equiv)

    row["faithfulness_cell"]               = _route_cell(is_equiv, expected_shape)
    row["faithfulness_equivalent"]         = is_equiv
    row["faithfulness_expected_shape"]     = expected_shape
    row["faithfulness_structural_verdict"] = struct_verdict
    row["faithfulness_structural_score"]   = f.get("faithfulness_structural_score")
    row["faithfulness_equiv_configs"]      = n_cfg
    row["faithfulness_equiv_passed"]       = n_pass
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_csv")
    ap.add_argument("--dataset", default="dataset")
    ap.add_argument("--equivalence", choices=["reuse", "recompute"], default="reuse")
    ap.add_argument("--output", default=None, help="default: overwrite input")
    args = ap.parse_args()

    out = args.output or args.input_csv
    tmp = out + ".tmp"
    by_vid = {v.variant_id: v for v in discover_variants(args.dataset)}
    slow_cache: dict[str, str] = {}
    n = miss = err = 0
    with open(args.input_csv, newline="") as rf, open(tmp, "w", newline="") as wf:
        r = csv.DictReader(rf)
        w = csv.DictWriter(wf, fieldnames=r.fieldnames)
        w.writeheader()
        for row in r:
            n += 1
            v = by_vid.get(row.get("variant_id", ""))
            if v is None:
                miss += 1
                w.writerow(row)
                continue
            if v.variant_id not in slow_cache:
                with open(v.slow_path) as sf:
                    slow_cache[v.variant_id] = sf.read()
            try:
                row = recompute_row(row, v, slow_cache[v.variant_id], args.equivalence)
            except Exception:
                err += 1  # leave row's faithfulness untouched on error
            w.writerow(row)
            if n % 500 == 0:
                print(f"  {n} rows...", flush=True)
    os.replace(tmp, out)
    print(f"done: {n} rows ({miss} variants not found, {err} errors) -> {out}",
          flush=True)


if __name__ == "__main__":
    main()
