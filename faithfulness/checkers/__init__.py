"""
faithfulness.checkers
---------------------
AST-based structural faithfulness checkers for all optimization patterns.

For each pattern, checks whether the model output applied the expected
structural transformation — not just whether the output is faster.

Uses pycparser for AST analysis with regex fallback when parsing fails.

Install:
    pip install pycparser

This package replaces the original monolithic `checkers.py`. The public API
is unchanged:

    from faithfulness.checkers import (
        CHECKERS, check_faithfulness, Verdict,
        FaithfulnessResult, PatternChecker,
    )

For instrumentation (e.g. `report_2x2.py`), `_parse` is also re-exported here
but the live function lives in `faithfulness.checkers._ast_helpers`. Anyone
monkey-patching `_parse` must patch the helpers module so the per-checker
helpers (`_calls_at_depth`, etc.) pick up the override.
"""

# Result types and base class
from ._base import (
    FaithfulnessResult,
    PatternChecker,
    Verdict,
    _result,
    _unknown,
)

# AST helpers + the pycparser availability flag.
# `_parse` is re-exported for backward-compatible imports
# (`from faithfulness.checkers import _parse`).
from ._ast_helpers import (
    HAS_PYCPARSER,
    _calls_at_depth,
    _if_stats,
    _loop_stats,
    _malloc_stats,
    _parse,
    _preprocess,
)

# Per-category checkers
from .algorithmic import AL1Checker, AL2Checker, AL3Checker, AL4Checker
from .composition import COMPChecker
from .control_flow import CF1Checker, CF2Checker, CF3Checker, CF4Checker
from .data_structure import DS1Checker, DS2Checker, DS3Checker, DS4Checker
from .human_style import (
    HR1Checker,
    HR2Checker,
    HR3Checker,
    HR4Checker,
    HR5Checker,
)
from .input_sensitive import (
    IS1Checker,
    IS2Checker,
    IS3Checker,
    IS4Checker,
    IS5Checker,
)
from .memory_io import MI1Checker, MI2Checker, MI3Checker, MI4Checker
from .semantic_redundancy import (
    SR1Checker,
    SR2Checker,
    SR3Checker,
    SR4Checker,
    SR5Checker,
)


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

CHECKERS: dict[str, PatternChecker] = {
    "SR-1":  SR1Checker(),
    "SR-2":  SR2Checker(),
    "SR-3":  SR3Checker(),
    "SR-4":  SR4Checker(),
    "SR-5":  SR5Checker(),
    "IS-1":  IS1Checker(),
    "IS-2":  IS2Checker(),
    "IS-3":  IS3Checker(),
    "IS-4":  IS4Checker(),
    "IS-5":  IS5Checker(),
    "CF-1":  CF1Checker(),
    "CF-2":  CF2Checker(),
    "CF-3":  CF3Checker(),
    "CF-4":  CF4Checker(),
    "HR-1":  HR1Checker(),
    "HR-2":  HR2Checker(),
    "HR-3":  HR3Checker(),
    "HR-4":  HR4Checker(),
    "HR-5":  HR5Checker(),
    "DS-1":  DS1Checker(),
    "DS-2":  DS2Checker(),
    "DS-3":  DS3Checker(),
    "DS-4":  DS4Checker(),
    "AL-1":  AL1Checker(),
    "AL-2":  AL2Checker(),
    "AL-3":  AL3Checker(),
    "AL-4":  AL4Checker(),
    "MI-1":  MI1Checker(),
    "MI-2":  MI2Checker(),
    "MI-3":  MI3Checker(),
    "MI-4":  MI4Checker(),
    "COMP":  COMPChecker(),
}


def check_faithfulness(
    pattern_id: str,
    slow_code: str,
    model_output: str,
    composition: list[str] | None = None,
) -> FaithfulnessResult:
    """
    Main entry point. Returns a FaithfulnessResult for the given pattern.

    Args:
        pattern_id:   e.g. "SR-1", "AL-3", "COMP"
        slow_code:    contents of slow.c
        model_output: the model's optimized C code
        composition:  for COMP only — list of constituent pattern IDs from metadata.json
    """
    checker = CHECKERS.get(pattern_id)
    if checker is None:
        return _unknown(f"no checker implemented for pattern '{pattern_id}'")
    try:
        if pattern_id == "COMP":
            return checker.check(slow_code, model_output, composition=composition)
        return checker.check(slow_code, model_output)
    except Exception as e:
        return _unknown(f"checker raised exception: {e}")


__all__ = [
    "CHECKERS",
    "FaithfulnessResult",
    "HAS_PYCPARSER",
    "PatternChecker",
    "Verdict",
    "check_faithfulness",
]
