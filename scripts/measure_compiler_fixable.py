"""Measure whether each variant's slow/fast performance gap survives compiler
optimization at various regimes.

For every variant under ``dataset/`` we compile ``slow.c`` + ``fast.c`` +
``helper.c`` + ``test.c`` as separate translation units (mirroring
``scripts/batch_test.py``) under five optimization regimes:

    -O0
    -O2 -fno-lto                  (current default the eval reports)
    -O3 -fno-lto
    -O3 -fno-lto -fno-math-errno -ffast-math
    -O3 -flto                     (link-time optimization — defeats the
                                   noinline-across-TU trick)

The binary built by test.c times slow and fast internally and prints
``slow_ms=... fast_ms=... correct=... speedup=...``.  We parse this line.

A variant is ``compiler_resistant`` at a given regime if the fast/slow
``speedup`` remains above the variant's per-pattern threshold. The
threshold defaults to ``RESISTANT_THRESHOLD`` (2.0) but is overridden
by the lower bound of ``metadata['expected_speedup_range']`` when that
field is present (e.g., ``"1.5x-3x"`` -> threshold 1.5). This honors
patterns whose fundamental ceiling is below 2x (e.g., HR-2 fuses 4
loops into 2, so the upper bound is ~2x) while keeping a strict
default for patterns that should achieve clear separation.

The headline finding the paper needs: how many variants does the
hand-asserted ``compiler_fixable: false`` flag in metadata.json misrepresent —
i.e. metadata says the compiler can NOT fix it, yet at -O3 the gap collapses
to <= 2x.

Output: ``dataset/measured_compiler_fixable.csv``.
"""
import os, sys, json, subprocess, tempfile, csv, multiprocessing
from collections import defaultdict

# Reuse extract_extern_decl from batch_test.  batch_test.py guards its driver
# code under ``if __name__ == "__main__":`` so import is side-effect free.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_test import extract_extern_decl, _C_HEADERS  # noqa: E402

# Optimization regimes to test.  Order matters for column order in the CSV.
REGIMES = [
    ("O0",            ["-O0"]),
    ("O2",            ["-O2", "-fno-lto"]),
    ("O3",            ["-O3", "-fno-lto"]),
    ("O3_fast_math",  ["-O3", "-fno-lto", "-fno-math-errno", "-ffast-math"]),
    ("O3_lto",        ["-O3", "-flto"]),
]

RESISTANT_THRESHOLD = 2.0
RUN_TIMEOUT_S = 60
COMPILE_TIMEOUT_S = 60


def _pattern_threshold(meta: dict) -> float:
    """Return the per-pattern resistance threshold.

    Threshold = min(RESISTANT_THRESHOLD, lower_bound_of_expected_range).
    The cap at 2.0x means a pattern that AIMS for a 16x speedup is still
    classified as "compiler fixes it" if measured speedup falls below 2x
    (the author thought the compiler couldn't fix it, but it did). The
    relaxation below 2.0x is only for patterns whose authorial lower bound
    is itself below 2x (e.g. HR-2 = "1.5x-3x" -> threshold 1.5; IS-2 =
    "1.1x-2x" -> 1.1) — those patterns have an inherent ceiling at or
    near 2x (e.g., HR-2 fuses 4 loops into 2 -> ~2x ceiling) so the
    default 2x threshold would over-flag them as compiler-fixable.
    """
    rng = meta.get("expected_speedup_range")
    if not rng:
        return RESISTANT_THRESHOLD
    try:
        low_str = str(rng).split("-")[0].strip().rstrip("xX")
        return min(RESISTANT_THRESHOLD, float(low_str))
    except (ValueError, IndexError):
        return RESISTANT_THRESHOLD


def _is_inverted_ct(meta: dict) -> bool:
    """True for constant-time-inverted patterns where slow.c is the
    correct CT formulation and the compiler BREAKS the CT discipline.
    For these, the resistance metric is correctness preservation, not
    wall-clock speedup — slow legitimately runs FASTER than fast."""
    return meta.get("pattern_type") == "constant_time_inverted"


def _empty_row_for(meta):
    row = {
        "variant_id": meta["variant_id"],
        "pattern_id": meta["pattern_id"],
        "category": meta["category"],
        "difficulty": meta["difficulty"],
        "metadata_compiler_fixable": meta.get("compiler_fixable", None),
        "resistance_threshold": _pattern_threshold(meta),
    }
    for tag, _ in REGIMES:
        row[f"slow_ms_{tag}"] = None
        row[f"fast_ms_{tag}"] = None
        row[f"speedup_{tag}"] = None
        row[f"resistant_{tag}"] = None  # tri-state: True / False / None(=failed)
    return row


def _prepare_sources(variant_dir, tmp):
    """Replicate batch_test's source-prep step: write slow.c / fast.c / test.c
    with extern decls swapped into test.c.  Returns paths and helper-existence.
    """
    slow = open(os.path.join(variant_dir, "slow.c")).read()
    fast = open(os.path.join(variant_dir, "fast.c")).read()
    test = open(os.path.join(variant_dir, "test.c")).read()
    if "SLOW_CODE_HERE" not in test:
        return None  # this variant doesn't have a placeholder-style test.c

    slow_decl = extract_extern_decl(slow)
    fast_decl = extract_extern_decl(fast)
    test_with_decls = (test
        .replace("// SLOW_CODE_HERE", slow_decl)
        .replace("// FAST_CODE_HERE", fast_decl))

    slow_src = os.path.join(tmp, "slow.c")
    fast_src = os.path.join(tmp, "fast.c")
    test_src = os.path.join(tmp, "test.c")
    with open(slow_src, "w") as f:
        f.write((_C_HEADERS if "#include" not in slow else "") + slow)
    with open(fast_src, "w") as f:
        f.write((_C_HEADERS if "#include" not in fast else "") + fast)
    with open(test_src, "w") as f:
        f.write(test_with_decls)

    helper_path = os.path.join(variant_dir, "helper.c")
    extra_tus = [helper_path] if os.path.exists(helper_path) else []
    return slow_src, fast_src, test_src, extra_tus


def measure_one(variant_dir):
    """Compile + run a single variant under every REGIME.

    Returns a dict with all CSV columns populated.  Failures are reported as
    ``None`` for the measurement fields; ``resistant_<tag>`` is also ``None``.
    """
    meta = json.load(open(os.path.join(variant_dir, "metadata.json")))
    row = _empty_row_for(meta)
    threshold = _pattern_threshold(meta)
    row["resistance_threshold"] = threshold

    with tempfile.TemporaryDirectory() as tmp:
        prepped = _prepare_sources(variant_dir, tmp)
        if prepped is None:
            # No placeholder test.c — leave row with all None measurements.
            return row
        slow_src, fast_src, test_src, extra_tus = prepped

        for tag, flags in REGIMES:
            bin_path = os.path.join(tmp, f"test_{tag}")
            cmd = (["gcc"] + flags + ["-o", bin_path,
                                       test_src, slow_src, fast_src]
                   + extra_tus + ["-lm"])
            try:
                cr = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=COMPILE_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                continue
            if cr.returncode != 0:
                continue

            try:
                rr = subprocess.run([bin_path], capture_output=True,
                                    text=True, timeout=RUN_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                continue
            if rr.returncode != 0:
                continue

            parts = dict(p.split("=") for p in rr.stdout.strip().split()
                         if "=" in p)
            try:
                slow_ms = float(parts.get("slow_ms", "nan"))
                fast_ms = float(parts.get("fast_ms", "nan"))
                speedup = float(parts.get("speedup", "nan"))
            except ValueError:
                continue

            row[f"slow_ms_{tag}"] = slow_ms
            row[f"fast_ms_{tag}"] = fast_ms
            row[f"speedup_{tag}"] = speedup
            # Inverted-CT patterns: resistant iff correct=1 (CT preserved).
            # The wall-clock metric is intentionally inverted; speedup < 1
            # is the design (compiler broke the CT path). The binary's
            # exit status reflects correctness; if we got here the run
            # exited 0 (returncode != 0 was filtered above).
            if _is_inverted_ct(meta):
                row[f"resistant_{tag}"] = True
            else:
                # Allow 5% noise margin around the threshold to handle
                # the measurement variance from running 8 workers in parallel
                # — without this margin, a variant whose true speedup hovers
                # at the threshold flips resistant/non-resistant across runs.
                row[f"resistant_{tag}"] = bool(speedup >= threshold * 0.95)

    return row


def _find_variants(dataset_dir):
    variants = []
    for root, dirs, files in os.walk(dataset_dir):
        # Skip the dataset/excluded/ subtree (compiler-fixable variants
        # filtered out of the active dataset; see scripts/filter_non_resistant.py).
        if "excluded" in dirs:
            dirs.remove("excluded")
        if ("metadata.json" in files and "slow.c" in files
                and "test.c" in files):
            variants.append(root)
    variants.sort()
    return variants


def _write_csv(rows, path):
    fieldnames = ["variant_id", "pattern_id", "category", "difficulty",
                  "metadata_compiler_fixable", "resistance_threshold"]
    for tag, _ in REGIMES:
        fieldnames += [f"slow_ms_{tag}", f"fast_ms_{tag}",
                       f"speedup_{tag}", f"resistant_{tag}"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _pct(num, denom):
    return (100.0 * num / denom) if denom else 0.0


def _print_summary(rows):
    # Group by pattern_id, compute % resistant at each regime.
    by_pattern = defaultdict(list)
    for r in rows:
        by_pattern[r["pattern_id"]].append(r)

    print("\n" + "=" * 110)
    print("PER-PATTERN COMPILER-RESISTANCE BY OPTIMIZATION REGIME")
    print("=" * 110)
    header = f"{'Pattern':<10} {'N':>4}"
    for tag, _ in REGIMES:
        header += f"  {'%res_' + tag:>14}"
    print(header)
    print("-" * 110)

    # Track patterns whose resistance crumbles between -O2 and the harder
    # regimes (-O3 ffast-math or -O3 -flto) — those are the patterns whose
    # "compiler-cannot-fix" claim is scope-limited.
    scope_limited = []
    for pid in sorted(by_pattern.keys()):
        prs = by_pattern[pid]
        n = len(prs)
        line = f"{pid:<10} {n:>4}"
        pcts = {}
        for tag, _ in REGIMES:
            measured = [r for r in prs if r[f"resistant_{tag}"] is not None]
            res = sum(1 for r in measured if r[f"resistant_{tag}"])
            pct = _pct(res, len(measured))
            pcts[tag] = pct
            line += f"  {pct:>13.1f}%"
        print(line)

        # Resistant at -O2 (>=50% of variants) but collapses at the harder
        # regimes (<50% resistant) — call that out.
        for harder in ("O3_fast_math", "O3_lto"):
            if pcts.get("O2", 0) >= 50.0 and pcts.get(harder, 100) < 50.0:
                scope_limited.append((pid, harder, pcts["O2"], pcts[harder]))
                break

    if scope_limited:
        print("\nPatterns whose compiler-resistance is SCOPE-LIMITED")
        print("  (resistant at -O2 but the compiler closes the gap at a "
              "stronger regime):")
        for pid, regime, p_o2, p_hard in scope_limited:
            print(f"  - {pid}: {p_o2:.0f}% resistant at -O2 -> "
                  f"{p_hard:.0f}% at -{regime}")
    else:
        print("\nNo patterns flagged as scope-limited (all stayed resistant "
              "across all -O3 variants tested).")


def _print_headline(rows):
    """The headline number: how many variants does metadata claim as
    compiler-resistant (compiler_fixable: false) but at -O3 the speedup
    collapses to <= 2x.
    """
    total = len(rows)
    claimed_resistant = [r for r in rows
                         if r["metadata_compiler_fixable"] is False]
    measured_o3 = [r for r in claimed_resistant
                   if r["resistant_O3"] is not None]
    misrepresented = [r for r in measured_o3 if r["resistant_O3"] is False]

    failed_o3 = sum(1 for r in rows if r["resistant_O3"] is None)

    print("\n" + "#" * 110)
    print("HEADLINE FINDING")
    print("#" * 110)
    print(f"Total variants                                : {total}")
    print(f"Variants where metadata says compiler-resistant"
          f" (compiler_fixable=false): {len(claimed_resistant)}")
    print(f"  ... successfully measured at -O3            : "
          f"{len(measured_o3)}")
    print(f"  ... of those, NOT resistant at -O3          : "
          f"{len(misrepresented)}  "
          f"({_pct(len(misrepresented), len(measured_o3)):.1f}% of measured)")
    print(f"Variants that failed to compile/run at -O3    : {failed_o3}")
    print()
    print(f">>> {len(misrepresented)} of {total} variants ({_pct(len(misrepresented), total):.1f}%) "
          f"are tagged compiler_fixable=false in metadata but the compiler "
          f"closes the gap at -O3.")
    print("#" * 110)


def main(dataset_dir, workers=None):
    variants = _find_variants(dataset_dir)
    n = len(variants)
    if n == 0:
        print(f"No variants found under {dataset_dir!r}")
        return

    if workers is None:
        workers = min(8, os.cpu_count() or 1)
    print(f"Measuring {n} variants across {len(REGIMES)} regimes "
          f"using {workers} workers ({n * len(REGIMES)} total builds)...")

    rows = []
    done = 0
    with multiprocessing.Pool(workers) as pool:
        for r in pool.imap_unordered(measure_one, variants):
            rows.append(r)
            done += 1
            if done % 25 == 0 or done == n:
                print(f"  [{done}/{n}] variants measured", flush=True)

    # Sort rows by variant_id for stable CSV ordering.
    rows.sort(key=lambda r: r["variant_id"])

    out_path = os.path.join(dataset_dir, "measured_compiler_fixable.csv")
    _write_csv(rows, out_path)
    print(f"\nWrote CSV: {out_path}")

    _print_summary(rows)
    _print_headline(rows)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dataset_dir", nargs="?", default="dataset")
    p.add_argument("--workers", type=int, default=None,
                   help="parallel workers (default: min(8, ncpu)). "
                        "Use 1 for noise-free per-variant ratios.")
    args = p.parse_args()
    main(args.dataset_dir, workers=args.workers)
