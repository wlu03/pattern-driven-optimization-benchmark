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
# Held-out (HO-*) checkers — added phase by phase per family.
from .held_out import (
    HOAL1Checker,
    HOAL2Checker,
    HOAL3Checker,
    HOAL4Checker,
    HOSR1Checker,
    HOSR2Checker,
    HOSR3Checker,
    HOSR4Checker,
    HOSR5Checker,
    HOSR6Checker,
    HOSR7Checker,
    HOCF1Checker,
    HOCF2Checker,
    HOCF3Checker,
    HOCF4Checker,
    HOCF5Checker,
    HODS1Checker,
    HODS2Checker,
    HODS3Checker,
    HODS4Checker,
    HODS5Checker,
    HODS6Checker,
    HOHR1Checker,
    HOHR2Checker,
    HOHR3Checker,
    HOHR4Checker,
    HOHR5Checker,
    HOIS1Checker,
    HOIS2Checker,
    HOIS3Checker,
    HOIS4Checker,
    HOIS5Checker,
    HOMI1Checker,
    HOMI2Checker,
    HOMI3Checker,
    HOMI4Checker,
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
    # Held-out (HO-*) — Algorithmic Inefficiency family.
    "HO-AL-1": HOAL1Checker(),
    "HO-AL-2": HOAL2Checker(),
    "HO-AL-3": HOAL3Checker(),
    "HO-AL-4": HOAL4Checker(),
    # Held-out (HO-*) — Semantic Redundancy family.
    "HO-SR-1": HOSR1Checker(),
    "HO-SR-2": HOSR2Checker(),
    "HO-SR-3": HOSR3Checker(),
    "HO-SR-4": HOSR4Checker(),
    "HO-SR-5": HOSR5Checker(),
    "HO-SR-6": HOSR6Checker(),
    "HO-SR-7": HOSR7Checker(),
    # Held-out (HO-*) — Control Flow family.
    "HO-CF-1": HOCF1Checker(),
    "HO-CF-2": HOCF2Checker(),
    "HO-CF-3": HOCF3Checker(),
    "HO-CF-4": HOCF4Checker(),
    "HO-CF-5": HOCF5Checker(),
    # Held-out (HO-*) — Data Structure Inefficiency family.
    "HO-DS-1": HODS1Checker(),
    "HO-DS-2": HODS2Checker(),
    "HO-DS-3": HODS3Checker(),
    "HO-DS-4": HODS4Checker(),
    "HO-DS-5": HODS5Checker(),
    "HO-DS-6": HODS6Checker(),
    # Held-out (HO-*) — Human-Style Antipatterns family.
    "HO-HR-1": HOHR1Checker(),
    "HO-HR-2": HOHR2Checker(),
    "HO-HR-3": HOHR3Checker(),
    "HO-HR-4": HOHR4Checker(),
    "HO-HR-5": HOHR5Checker(),
    # Held-out (HO-*) — Input-Sensitive Inefficiency family.
    "HO-IS-1": HOIS1Checker(),
    "HO-IS-2": HOIS2Checker(),
    "HO-IS-3": HOIS3Checker(),
    "HO-IS-4": HOIS4Checker(),
    "HO-IS-5": HOIS5Checker(),
    # Held-out (HO-*) — Memory & IO family.
    "HO-MI-1": HOMI1Checker(),
    "HO-MI-2": HOMI2Checker(),
    "HO-MI-3": HOMI3Checker(),
    "HO-MI-4": HOMI4Checker(),
}


def _heldout_fallback_check(slow_code: str,
                             model_output: str) -> FaithfulnessResult:
    """Structural fallback for HO-* patterns without a dedicated checker.

    Per-pattern AST-level checkers for the 36 held-out patterns are not
    yet authored (the held-out wave was added after the base-pattern
    checker registry). Until they are, return a coarse but useful
    verdict based on whether the model emitted code structurally
    different from slow.c.

    Verdicts:
      - "unfaithful" + score 0.0  if model_output is essentially a
        copy of slow.c (no transformation attempted)
      - "partial" + score 0.5     if model_output differs from slow.c
        but we cannot judge whether the difference is the expected
        transformation
      - never returns "faithful" — that requires a per-pattern checker
        and would be misleading without one
    """
    import re

    def _normalize(s: str) -> str:
        # Strip comments, whitespace, blank lines for a coarse
        # is-this-the-same-code? comparison.
        s = re.sub(r"//[^\n]*", "", s)
        s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
        return "".join(s.split())

    slow_n = _normalize(slow_code)
    out_n = _normalize(model_output)
    if not out_n:
        return FaithfulnessResult(
            Verdict.UNFAITHFUL, 0.0,
            "held-out fallback: model output is empty",
            checks_passed=[], checks_failed=["non_empty_output"],
        )
    # Substring containment heuristic — if the model just wrapped slow_code
    # in a stub, the slow body still appears verbatim.
    if (slow_n and slow_n in out_n) or slow_n == out_n:
        return FaithfulnessResult(
            Verdict.UNFAITHFUL, 0.0,
            "held-out fallback: model output contains slow body verbatim "
            "(no transformation attempted)",
            checks_passed=[], checks_failed=["any_transformation"],
        )
    # Different from slow but no per-pattern checker available — verdict
    # is structurally indeterminate. Mark as UNKNOWN (not FAITHFUL/PARTIAL)
    # so downstream analyses don't mistake the fallback for a real verdict.
    return FaithfulnessResult(
        Verdict.UNKNOWN, 0.5,
        "held-out fallback: model output differs from slow.c but no "
        "pattern-specific checker is implemented — verdict is "
        "structurally indeterminate (counted toward STRUCTURAL_ONLY)",
        checks_passed=[], checks_failed=[],
    )


def check_faithfulness(
    pattern_id: str,
    slow_code: str,
    model_output: str,
    composition: list[str] | None = None,
) -> FaithfulnessResult:
    """
    Main entry point. Returns a FaithfulnessResult for the given pattern.

    Args:
        pattern_id:   e.g. "SR-1", "AL-3", "COMP", "HO-CF-2"
        slow_code:    contents of slow.c
        model_output: the model's optimized C code
        composition:  for COMP only — list of constituent pattern IDs from metadata.json

    Held-out (HO-*) patterns fall through to a coarse structural fallback
    when no dedicated checker is registered; see _heldout_fallback_check.
    """
    checker = CHECKERS.get(pattern_id)
    if checker is not None:
        try:
            if pattern_id == "COMP":
                return checker.check(slow_code, model_output, composition=composition)
            return checker.check(slow_code, model_output)
        except Exception as e:
            return _unknown(f"checker raised exception: {e}")

    # Held-out patterns: structural fallback (better than "unknown" because
    # it can still catch the "model returned slow.c verbatim" failure mode)
    if pattern_id.startswith("HO-"):
        try:
            return _heldout_fallback_check(slow_code, model_output)
        except Exception as e:
            return _unknown(f"heldout fallback raised: {e}")

    return _unknown(f"no checker implemented for pattern '{pattern_id}'")


__all__ = [
    "CHECKERS",
    "FaithfulnessResult",
    "HAS_PYCPARSER",
    "PatternChecker",
    "Verdict",
    "check_faithfulness",
]
