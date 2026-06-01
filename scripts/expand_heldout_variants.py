"""expand_heldout_variants.py
-----------------------------
Expand each held-out pattern's single _v000 variant into multiple variants
by varying problem size (N) and the random seed used to initialize inputs.
Function names and the variant_id metadata are updated accordingly.

Usage:
    python3 scripts/expand_heldout_variants.py --variants-per-pattern 5

By default produces variant_num 0..N-1 for every pattern under
dataset/held_out/HO_*/. _v000 is left untouched (it's the original); the
script adds _v001 through _v(N-1).

What changes between variants:
  - Function symbol suffix: slow_ho_cf2_v000 -> slow_ho_cf2_v001 (etc.)
  - srand(42) seed value is rotated per variant
  - #define N is scaled (where present) by a per-variant factor
  - metadata.json: variant_id, variant_desc updated; everything else
    preserved (pattern_id, category, expected_speedup_range, citation, ...)

What does NOT change:
  - The algorithm / inefficiency itself (preserves the micro-skill tested)
  - Data type (changing dtype would invalidate per-pattern tolerances)
  - File structure (still slow.c / fast.c / test.c / metadata.json)
"""
import argparse
import json
import os
import re
import shutil
import sys


# Per-variant (seed, n_scale) — index 1..4 (0 is unchanged)
VARIANT_DELTAS = [
    None,                    # v000: original
    (43,  0.5),              # v001: smaller, different seed
    (44,  1.5),              # v002: larger, different seed
    (45,  2.0),              # v003: much larger, different seed
    (46,  0.7),              # v004: medium, different seed
]


def patch_symbols(text: str, old_suffix: str, new_suffix: str) -> str:
    """Rename suffix in any function symbol referenced as _v000."""
    # Match `_v000` only as a complete word boundary (not inside arbitrary
    # identifiers like _v0001234, but the typical use is the suffix marker).
    return re.sub(rf"_{old_suffix}\b", f"_{new_suffix}", text)


def patch_srand_seed(test_text: str, seed: int) -> str:
    """Replace the seed in srand(...) with the given seed."""
    return re.sub(r"srand\(\s*\d+\s*\)", f"srand({seed})", test_text)


def patch_n_define(test_text: str, scale: float) -> str:
    """Scale the #define N <integer> by the given factor."""
    def repl(m):
        n = int(m.group(2))
        new = max(64, int(n * scale))  # don't let N go too small
        return f"{m.group(1)}{new}"
    return re.sub(r"(^#define\s+N\s+)(\d+)", repl, test_text, flags=re.M)


def expand_pattern(variant_dir: str, n_variants: int) -> int:
    """Generate _v001..._v(n_variants-1) from _v000 in the parent of variant_dir.

    Returns count of variants created.
    """
    if not variant_dir.endswith("_v000"):
        print(f"  SKIP: not a _v000 dir: {variant_dir}", file=sys.stderr)
        return 0

    parent = os.path.dirname(variant_dir)
    base = os.path.basename(variant_dir)  # e.g. HO-CF-2_v000
    pattern_id = base[:-len("_v000")]    # e.g. HO-CF-2

    # Read source files
    slow_src = open(os.path.join(variant_dir, "slow.c")).read()
    fast_src = open(os.path.join(variant_dir, "fast.c")).read()
    test_src = open(os.path.join(variant_dir, "test.c")).read()
    meta = json.load(open(os.path.join(variant_dir, "metadata.json")))
    helper_path = os.path.join(variant_dir, "helper.c")
    helper_src = open(helper_path).read() if os.path.exists(helper_path) else None

    created = 0
    for vnum in range(1, n_variants):
        if vnum >= len(VARIANT_DELTAS):
            break
        delta = VARIANT_DELTAS[vnum]
        seed, scale = delta
        new_suffix = f"v{vnum:03d}"
        new_dir = os.path.join(parent, f"{pattern_id}_{new_suffix}")
        if os.path.isdir(new_dir):
            # Already exists — skip (idempotent)
            continue
        os.makedirs(new_dir, exist_ok=True)

        # Patch sources
        new_slow = patch_symbols(slow_src, "v000", new_suffix)
        new_fast = patch_symbols(fast_src, "v000", new_suffix)
        new_test = patch_symbols(test_src, "v000", new_suffix)
        new_test = patch_srand_seed(new_test, seed)
        new_test = patch_n_define(new_test, scale)

        open(os.path.join(new_dir, "slow.c"), "w").write(new_slow)
        open(os.path.join(new_dir, "fast.c"), "w").write(new_fast)
        open(os.path.join(new_dir, "test.c"), "w").write(new_test)
        if helper_src is not None:
            new_helper = patch_symbols(helper_src, "v000", new_suffix)
            open(os.path.join(new_dir, "helper.c"), "w").write(new_helper)

        # Patch metadata
        new_meta = dict(meta)
        new_meta["variant_id"] = f"{pattern_id}_{new_suffix}"
        orig_desc = meta.get("variant_desc", "")
        new_meta["variant_desc"] = (
            f"{orig_desc} (variant {vnum}: seed={seed}, n_scale={scale}x)"
            if orig_desc else
            f"variant {vnum}: seed={seed}, n_scale={scale}x"
        )
        json.dump(new_meta, open(os.path.join(new_dir, "metadata.json"), "w"),
                  indent=2)
        created += 1
        print(f"  + {pattern_id}_{new_suffix}  (seed={seed}, n_scale={scale}x)")
    return created


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--variants-per-pattern", type=int, default=5,
                   help="Total variants to produce per pattern, including "
                        "the existing _v000 (default 5 -> _v000.._v004)")
    p.add_argument("--held-out-dir", default="dataset/held_out")
    args = p.parse_args()

    if args.variants_per_pattern < 2:
        print("Nothing to do (need >= 2 variants).")
        return
    if args.variants_per_pattern > len(VARIANT_DELTAS):
        print(f"WARNING: --variants-per-pattern={args.variants_per_pattern} "
              f"exceeds the VARIANT_DELTAS table size "
              f"({len(VARIANT_DELTAS)}). Capping at "
              f"{len(VARIANT_DELTAS)}.")

    base_dirs = []
    for root, dirs, files in os.walk(args.held_out_dir):
        if "metadata.json" in files and root.endswith("_v000"):
            base_dirs.append(root)
    base_dirs.sort()

    print(f"Expanding {len(base_dirs)} held-out patterns to "
          f"~{args.variants_per_pattern} variants each...\n")
    total_created = 0
    for d in base_dirs:
        total_created += expand_pattern(d, args.variants_per_pattern)
    print(f"\nDone. Created {total_created} new variants.")


if __name__ == "__main__":
    main()
