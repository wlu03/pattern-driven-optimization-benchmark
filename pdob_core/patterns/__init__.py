from ._entry import PatternEntry
from ._preamble import _HARNESS_PREAMBLE, _apply_preamble
from .semantic_redundancy import SR_PATTERNS
from .input_sensitive import IS_PATTERNS
from .control_flow import CF_PATTERNS
from .human_style import HR_PATTERNS
from .data_structure import DS_PATTERNS
from .algorithmic import AL_PATTERNS
from .memory_io import MI_PATTERNS


# All 27 patterns — order matches the legacy patterns.py list and is used as
# a stable index across the dataset / evaluator / variant-generator pipelines.
PATTERNS = (
    SR_PATTERNS
    + IS_PATTERNS
    + CF_PATTERNS
    + HR_PATTERNS
    + DS_PATTERNS
    + AL_PATTERNS
    + MI_PATTERNS
)


# ─────────────────────────────────────────────────────────────────────────
# Post-process: inject the multi-input + tolerance preamble into every
# harness.  Substitutions made by _apply_preamble:
#   int n = NNN;       -> int n = _bench_n(NNN);     (BENCH_N env var)
#   srand(42);         -> srand(_bench_seed(42));    (BENCH_SEED env var)
# Plus injection of helper functions:
#   _bench_n, _bench_seed, _bench_dist, _bench_fill_dist[_int], _bench_close
# When BENCH_* env vars are unset, behavior is byte-identical to pre-patch.
# ─────────────────────────────────────────────────────────────────────────
for _p in PATTERNS:
    _p.test_harness = _apply_preamble(_p.test_harness)
del _p


__all__ = ["PATTERNS", "PatternEntry"]
