"""Pattern variant generators package.

Exposes the same ``GENERATORS`` dict and ``generate_dataset`` function that
previously lived at module scope in ``generate_variants.py``.  The CLI in
``generate_variants.py`` is now a thin wrapper that delegates here.

Each per-category submodule contains one or more ``*_Generator`` classes
extracted verbatim from the original monolithic script.
"""

import csv
import json
import os
from collections import Counter

from ._dataset_tolerance import (
    _DATASET_TOL_HELPER,
    _DTYPE_TOL,
    _TOL_REWRITES,
    _apply_dataset_tolerance,
    _inject_tol_helper,
)
from ._shared import (
    BINARY_OPS,
    DTYPES,
    PatternTemplate,
    REDUCTION_OPS,
    SAFE_AOS_FIELD_COUNT,
    UNARY_MATH_FNS,
    VariantMetadata,
)
from .algorithmic import (
    AL1_Generator,
    AL2_Generator,
    AL3_Generator,
    AL4_Generator,
)
from .composition import ComposedGenerator
from .control_flow import (
    CF1_Generator,
    CF2_Generator,
    CF3_Generator,
    CF4_Generator,
)
from .data_structure import (
    DS1_Generator,
    DS2_Generator,
    DS3_Generator,
    DS4_Generator,
)
from .human_style import (
    HR1_Generator,
    HR2_Generator,
    HR3_Generator,
    HR4_Generator,
    HR5_Generator,
)
from .input_sensitive import (
    IS1_Generator,
    IS2_Generator,
    IS3_Generator,
    IS4_Generator,
    IS5_Generator,
)
from .memory_io import (
    MI1_Generator,
    MI2_Generator,
    MI3_Generator,
    MI4_Generator,
)
from .semantic_redundancy import (
    SR1_Generator,
    SR2_Generator,
    SR3_Generator,
    SR4_Generator,
    SR5_Generator,
)


# Ordered registry — order MUST match the original ``generate_variants.py``
# so that ``--patterns all`` iterates over generators in the same sequence
# and produces byte-identical metadata indices on disk.
GENERATORS = {
    "SR-1": SR1_Generator(),
    "SR-2": SR2_Generator(),
    "SR-3": SR3_Generator(),
    "SR-4": SR4_Generator(),
    "SR-5": SR5_Generator(),
    "IS-1": IS1_Generator(),
    "IS-2": IS2_Generator(),
    "IS-3": IS3_Generator(),
    "IS-4": IS4_Generator(),
    "IS-5": IS5_Generator(),
    "CF-1": CF1_Generator(),
    "CF-2": CF2_Generator(),
    "CF-3": CF3_Generator(),
    "CF-4": CF4_Generator(),
    "HR-1": HR1_Generator(),
    "HR-2": HR2_Generator(),
    "HR-3": HR3_Generator(),
    "HR-4": HR4_Generator(),
    "HR-5": HR5_Generator(),
    "DS-1": DS1_Generator(),
    "DS-2": DS2_Generator(),
    "DS-3": DS3_Generator(),
    "DS-4": DS4_Generator(),
    "AL-1": AL1_Generator(),
    "AL-2": AL2_Generator(),
    "AL-3": AL3_Generator(),
    "AL-4": AL4_Generator(),
    "MI-1": MI1_Generator(),
    "MI-2": MI2_Generator(),
    "MI-3": MI3_Generator(),
    "MI-4": MI4_Generator(),
    "COMP": ComposedGenerator(),
}


def generate_dataset(patterns: str, n_variants: int, output_dir: str, base_seed: int = 42):
    """Generate the full dataset."""
    os.makedirs(output_dir, exist_ok=True)

    # Determine which generators to use
    if patterns == "all":
        gens = list(GENERATORS.items())
    elif "-" in patterns:
        gens = [(patterns, GENERATORS[patterns])]
    else:
        # Category prefix like "SR", "IS", "AL"
        gens = [(k, v) for k, v in GENERATORS.items() if k.startswith(patterns)]

    all_metadata = []
    total = 0

    for pat_id, gen in gens:
        pat_dir = os.path.join(output_dir, pat_id.replace("-", "_"))
        os.makedirs(pat_dir, exist_ok=True)

        for i in range(n_variants):
            seed = base_seed + hash(pat_id) + i * 7919  # Deterministic but varied
            result = gen.generate(i, seed)

            vid = result["metadata"]["variant_id"]
            var_dir = os.path.join(pat_dir, vid)
            os.makedirs(var_dir, exist_ok=True)

            # Write files.  test.c gets the standardized _bench_close helper
            # injected (Issue B / item 10) so future generators or hand-edits
            # can use a uniform combined absolute+relative tolerance check.
            with open(os.path.join(var_dir, "slow.c"), "w") as f:
                f.write(result["slow_code"])
            with open(os.path.join(var_dir, "fast.c"), "w") as f:
                f.write(result["fast_code"])
            with open(os.path.join(var_dir, "test.c"), "w") as f:
                f.write(_apply_dataset_tolerance(
                    result["test_code"],
                    dtype=result["metadata"].get("dtype", "double"),
                ))
            if "helper_code" in result:
                with open(os.path.join(var_dir, "helper.c"), "w") as f:
                    f.write(result["helper_code"])
            with open(os.path.join(var_dir, "metadata.json"), "w") as f:
                json.dump(result["metadata"], f, indent=2)

            all_metadata.append(result["metadata"])
            total += 1

    # Write master index
    with open(os.path.join(output_dir, "index.json"), "w") as f:
        json.dump({
            "total_variants": total,
            "patterns": list(set(m["pattern_id"] for m in all_metadata)),
            "categories": list(set(m["category"] for m in all_metadata)),
            "variants": all_metadata,
        }, f, indent=2)

    # Write CSV summary
    with open(os.path.join(output_dir, "index.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "variant_id", "pattern_id", "category", "pattern_name",
            "variant_desc", "dtype", "difficulty",
            "compiler_fixable", "expected_speedup_range"
        ])
        writer.writeheader()
        for m in all_metadata:
            writer.writerow({k: m[k] for k in writer.fieldnames})

    print(f"Generated {total} variants across {len(gens)} patterns in {output_dir}/")
    print(f"  Index: {output_dir}/index.json")
    print(f"  CSV:   {output_dir}/index.csv")

    # Print summary
    by_pattern = Counter(m["pattern_id"] for m in all_metadata)
    by_diff = Counter(m["difficulty"] for m in all_metadata)
    print(f"\n  By pattern: {dict(by_pattern)}")
    print(f"  By difficulty: {dict(by_diff)}")


__all__ = [
    # Public API
    "generate_dataset",
    "GENERATORS",
    "VariantMetadata",
    "PatternTemplate",
    # Shared constants (re-exported for compatibility)
    "DTYPES",
    "BINARY_OPS",
    "UNARY_MATH_FNS",
    "REDUCTION_OPS",
    "SAFE_AOS_FIELD_COUNT",
    # Tolerance helpers (re-exported for compatibility)
    "_DATASET_TOL_HELPER",
    "_DTYPE_TOL",
    "_TOL_REWRITES",
    "_inject_tol_helper",
    "_apply_dataset_tolerance",
    # Generator classes
    "SR1_Generator", "SR2_Generator", "SR3_Generator", "SR4_Generator", "SR5_Generator",
    "IS1_Generator", "IS2_Generator", "IS3_Generator", "IS4_Generator", "IS5_Generator",
    "CF1_Generator", "CF2_Generator", "CF3_Generator", "CF4_Generator",
    "HR1_Generator", "HR2_Generator", "HR3_Generator", "HR4_Generator", "HR5_Generator",
    "DS1_Generator", "DS2_Generator", "DS3_Generator", "DS4_Generator",
    "AL1_Generator", "AL2_Generator", "AL3_Generator", "AL4_Generator",
    "MI1_Generator", "MI2_Generator", "MI3_Generator", "MI4_Generator",
    "ComposedGenerator",
]
