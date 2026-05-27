"""Standardised test.c tolerance helper injection.

Extracted verbatim from the original ``generate_variants.py`` (lines 44-139).
Used by :func:`generators.generate_dataset` to post-process every generator's
emitted ``test_code`` before writing ``test.c`` to disk.

Public API (kept identical to the original module-level names so any caller
that did ``from generate_variants import _apply_dataset_tolerance`` continues
to work):

    _DATASET_TOL_HELPER    -- C source for the ``_bench_close`` helper
    _inject_tol_helper     -- splice the helper after the last #include
    _apply_dataset_tolerance -- inject helper + rewrite common tolerance shapes
"""

import re


# ─────────────────────────────────────────────────────────────────────────
# Standardised correctness check (Issue B / item 10)
#
# Previously each generator emitted its own tolerance expression, e.g.
#   fabs(slow - fast) > 1e-6                 — absolute only, wrong for big
#   fabs(slow - fast) / (fabs(slow)+1e-12)   — relative only, wrong for tiny
# The combined absolute+relative form below is correct on both extremes:
#   |a - b| <= atol + rtol * |b|
#
# NOTE: The 590 dataset variants already on disk under dataset/ have the
# OLD per-generator tolerance baked into their test.c.  This change only
# affects newly-generated variants — re-running this script
# (`python3 generate_variants.py --patterns all --variants 20 --output dataset/`)
# will rewrite those test.c files with the new standardized tolerance.
# ─────────────────────────────────────────────────────────────────────────
_DATASET_TOL_HELPER = r"""/* ── standardized correctness check (auto-injected) ─────────────────── */
static inline int _bench_close(double a, double b, double atol, double rtol) {
    double d = a - b; if (d < 0) d = -d;
    double mb = b; if (mb < 0) mb = -mb;
    return d <= atol + rtol * mb;
}
/* ── end ────────────────────────────────────────────────────────────── */
"""

# Default tolerances per dtype.  Generators that want tighter/looser bounds
# can pass them explicitly via the regex substitution, but these defaults
# cover the common cases.
_DTYPE_TOL = {
    "double": (1e-9, 1e-6),
    "float":  (1e-6, 1e-4),
    "int":    (0,     0),   # exact match for integer dtypes
}


def _inject_tol_helper(test_code: str) -> str:
    """Inject `_bench_close` after the last #include in a test.c template.

    Idempotent: if `_bench_close` is already present, returns unchanged.
    """
    if "_bench_close" in test_code:
        return test_code
    lines = test_code.split('\n')
    last_inc = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('#include'):
            last_inc = i
    if last_inc >= 0:
        lines.insert(last_inc + 1, _DATASET_TOL_HELPER)
    return '\n'.join(lines)


# Pre-compiled patterns for the common tolerance check shapes used across
# the 59 test_code blocks.  Each pattern captures (lhs, rhs) of the diff and
# is rewritten to a `!_bench_close(lhs, rhs, atol, rtol)` form.  The atol/
# rtol are chosen based on the original tolerance present so we preserve
# (or slightly relax) the strictness of each individual generator.
_TOL_REWRITES = [
    # Pattern: if(fabs((double)(a - b)) > TOL) {{ ... }}    — pure absolute
    (re.compile(r'fabs\(\(double\)\(([^()]+?)\s*-\s*([^()]+?)\)\)\s*>\s*([0-9.eE+-]+(?:f)?)'),
     lambda m: f'!_bench_close((double)({m.group(1)}), (double)({m.group(2)}), {m.group(3)}, 1e-6)'),

    # Pattern: fabs(a - b) > TOL                            — pure absolute (no cast)
    (re.compile(r'fabs\(([A-Za-z_][\w\[\]]*(?:\[[^\]]+\])?)\s*-\s*([A-Za-z_][\w\[\]]*(?:\[[^\]]+\])?)\)\s*>\s*([0-9.eE+-]+(?:f)?)'),
     lambda m: f'!_bench_close({m.group(1)}, {m.group(2)}, {m.group(3)}, 1e-6)'),
]


def _apply_dataset_tolerance(test_code: str, dtype: str = "double") -> str:
    """Standardize tolerance checks in a generated test.c and inject the
    `_bench_close` helper.

    Two transformations:
      1. Inject `_bench_close` helper after the includes.
      2. Rewrite the most common per-generator tolerance shapes to use it.
         We pick atol/rtol based on the per-dtype default (double: 1e-9 /
         1e-6; float: 1e-6 / 1e-4; int: exact match).  Generators that
         use a one-off custom tolerance keep it (we only match the
         common "fabs(a - b) > TOL" / "fabs((double)(a - b)) > TOL"
         forms — anything more elaborate is left to the generator).
    """
    test_code = _inject_tol_helper(test_code)
    atol, rtol = _DTYPE_TOL.get(dtype, _DTYPE_TOL["double"])
    # Shape 1: fabs((double)(LHS - RHS)) > TOL   — pure-absolute check.
    # Replace with combined atol+rtol form using _bench_close.
    test_code = re.sub(
        r'fabs\(\(double\)\(([A-Za-z_][\w\[\]]*)\s*-\s*([A-Za-z_][\w\[\]]*)\)\)\s*>\s*([0-9.eE+-]+f?)',
        lambda m: f'!_bench_close((double)({m.group(1)}), (double)({m.group(2)}), {m.group(3)}, {rtol})',
        test_code,
    )
    # Shape 2: fabs(LHS - RHS) > TOL  (no cast).  Same rewrite.
    test_code = re.sub(
        r'(?<!_bench_close\()fabs\(([A-Za-z_][\w\[\]]*)\s*-\s*([A-Za-z_][\w\[\]]*)\)\s*>\s*([0-9.eE+-]+f?)',
        lambda m: f'!_bench_close({m.group(1)}, {m.group(2)}, {m.group(3)}, {rtol})',
        test_code,
    )
    return test_code
