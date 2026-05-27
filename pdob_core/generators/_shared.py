"""Shared constants and helpers for pattern variant generators.

Contains the things that were defined at module scope in the original
``generate_variants.py`` and are imported by every per-category module:

  * DTYPES, BINARY_OPS, UNARY_MATH_FNS, REDUCTION_OPS, SAFE_AOS_FIELD_COUNT
  * VariantMetadata dataclass
  * PatternTemplate base class

The tolerance-injection helpers (``_DATASET_TOL_HELPER``, ``_inject_tol_helper``,
``_apply_dataset_tolerance``) live in :mod:`generators._dataset_tolerance`.
"""

from dataclasses import dataclass
from typing import List


DTYPES = {
    "int":    {"fmt": "%d",    "zero": "0",    "cast": "(int)",    "suffix": ""},
    "float":  {"fmt": "%f",    "zero": "0.0f", "cast": "(float)",  "suffix": "f"},
    "double": {"fmt": "%lf",   "zero": "0.0",  "cast": "(double)", "suffix": ""},
}


# Minimum struct field count for AoS benchmarks.
# 32 float fields = 128 bytes/element; 32 double fields = 256 bytes/element.
# This ensures the AoS stride penalty is reliably measurable even on Apple Silicon
# (high memory bandwidth + hardware prefetch can mask narrow structs at -O3).
SAFE_AOS_FIELD_COUNT = 32

BINARY_OPS = [
    ("+", "add"), ("-", "sub"), ("*", "mul"),
]

UNARY_MATH_FNS = [
    ("sin", "math"),  ("cos", "math"),  ("sqrt", "math"),
    ("exp", "math"),  ("log", "math"),  ("fabs", "math"),
]

REDUCTION_OPS = [
    ("+=", "sum"), ("*=", "product"),
    ("= fmax({acc}, {val})", "max"), ("= fmin({acc}, {val})", "min"),
]

# ── Metadata ──────────────────────────────────────────────────

@dataclass
class VariantMetadata:
    pattern_id: str              # e.g., "SR-1"
    variant_id: str              # e.g., "SR-1_v007"
    category: str                # e.g., "Semantic Redundancy"
    pattern_name: str            # e.g., "Loop-Invariant Semantic Computation"
    variant_desc: str            # What varies in this instance
    dtype: str                   # e.g., "double"
    difficulty: str              # "easy", "medium", "hard"
    compiler_fixable: bool       # Can -O3 fix this?
    num_loops: int               # Loop nesting depth
    num_arrays: int              # Number of input arrays
    lines_of_code: int           # Approximate LOC of slow version
    expected_speedup_range: str  # e.g., "2x-10x" or "100x+"
    composition: List[str]       # If composed, list of pattern IDs


class PatternTemplate:
    """Base class for pattern variant generators."""

    def __init__(self, pattern_id: str, category: str, name: str):
        self.pattern_id = pattern_id
        self.category = category
        self.name = name

    def generate(self, variant_num: int, seed: int) -> dict:
        """Returns dict with keys: slow_code, fast_code, test_code, metadata"""
        raise NotImplementedError
