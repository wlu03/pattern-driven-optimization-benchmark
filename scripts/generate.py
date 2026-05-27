#!/usr/bin/env python3
"""Pattern Variant Generator for Code Optimization Benchmark — CLI entry point.

The generator logic lives in the :mod:`generators` package (one submodule per
pattern category).  This script is a thin argparse wrapper around
:func:`generators.generate_dataset`.

Generates N distinct slow/fast C code pairs for each taxonomy pattern by
varying dimensionality, dtype, operation kind, loop structure, code
complexity, and pattern composition.  Each pair includes:

  - slow.c: The inefficient version
  - fast.c: The hand-optimized reference
  - test.c: Test harness with verification (auto-injected _bench_close helper)
  - helper.c: Optional separate-TU noinline helpers (when needed)
  - metadata.json: Pattern ID, difficulty, description

Usage:
    python3 scripts/generate.py --patterns all --variants 20 --output dataset/
    python3 scripts/generate.py --patterns SR  --variants 50 --output dataset/
    python3 scripts/generate.py --patterns SR-1 --variants 10 --output dataset/
"""

import argparse
import os
import sys

# Make the repo root importable so ``pdob_core`` resolves when this script
# is run directly (``python3 scripts/generate.py ...``).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdob_core.generators import generate_dataset  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Generate pattern variant dataset")
    parser.add_argument("--patterns", default="all",
                        help="Which patterns: 'all', category prefix 'SR', or specific 'SR-1'")
    parser.add_argument("--variants", type=int, default=20,
                        help="Number of variants per pattern (default: 20)")
    parser.add_argument("--output", default="dataset",
                        help="Output directory (default: dataset/)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    generate_dataset(args.patterns, args.variants, args.output, args.seed)


if __name__ == "__main__":
    main()
