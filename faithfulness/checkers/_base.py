"""
_base.py
--------
Base class and result types for structural faithfulness checkers.

Verdict layers (lowest to highest):
  - `Verdict` + `FaithfulnessResult` — single-axis output of one structural
    checker. The 27 per-pattern checkers all return this.
  - `TwoAxisVerdict` — cascade output combining a structural check with a
    semantic-equivalence check (see faithfulness/equivalence.py). Addresses
    the "different-but-equivalent transformation" problem: a model that hits
    the expected speedup via a different valid mechanism lands in
    FAITHFUL_ALTERNATIVE instead of being conflated with UNFAITHFUL.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Single-axis (structural) result types
# ─────────────────────────────────────────────────────────────────────────────

class Verdict:
    FAITHFUL   = "faithful"
    UNFAITHFUL = "unfaithful"
    PARTIAL    = "partial"
    UNKNOWN    = "unknown"   # parse failure or checker not implemented


@dataclass
class FaithfulnessResult:
    verdict:       str
    score:         float          # 0.0 – 1.0
    explanation:   str
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict":       self.verdict,
            "score":         self.score,
            "explanation":   self.explanation,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Two-axis verdict (cascade output)
# ─────────────────────────────────────────────────────────────────────────────

class Cell:
    FAITHFUL              = "FAITHFUL"               # expected transform AND equivalent
    FAITHFUL_ALTERNATIVE  = "FAITHFUL_ALTERNATIVE"   # equivalent via different transform
    STRUCTURAL_ONLY       = "STRUCTURAL_ONLY"        # has expected shape but breaks correctness
    FAILED                = "FAILED"                 # neither


@dataclass
class TwoAxisVerdict:
    """Cascade verdict: (semantic-equivalence × expected-transformation-applied)."""
    equivalent:     bool
    expected_shape: bool
    source:         str = "cascade"   # 'cascade' | 'structural' | 'differential' | 'judge'
    structural_result:  Optional[FaithfulnessResult] = None
    equivalence_result: Optional[object] = None   # EquivalenceResult; typed `object` to avoid circular import

    @property
    def cell(self) -> str:
        if self.equivalent and self.expected_shape:     return Cell.FAITHFUL
        if self.equivalent and not self.expected_shape: return Cell.FAITHFUL_ALTERNATIVE
        if not self.equivalent and self.expected_shape: return Cell.STRUCTURAL_ONLY
        return Cell.FAILED

    def to_dict(self) -> dict:
        d = {"cell": self.cell, "equivalent": self.equivalent,
             "expected_shape": self.expected_shape, "source": self.source}
        if self.structural_result is not None:
            d["structural"] = self.structural_result.to_dict()
        if self.equivalence_result is not None and hasattr(self.equivalence_result, "to_dict"):
            d["equivalence"] = self.equivalence_result.to_dict()
        return d


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build result from passed/failed lists
# ─────────────────────────────────────────────────────────────────────────────

def _result(passed: list[str], failed: list[str]) -> FaithfulnessResult:
    total = len(passed) + len(failed)
    if total == 0:
        return FaithfulnessResult(Verdict.UNKNOWN, 0.0, "no checks ran", passed, failed)
    score = len(passed) / total
    if score == 1.0:
        verdict, expl = Verdict.FAITHFUL,   "all structural checks passed"
    elif score == 0.0:
        verdict, expl = Verdict.UNFAITHFUL, "no structural checks passed"
    else:
        verdict, expl = Verdict.PARTIAL,    f"{len(passed)}/{total} checks passed"
    return FaithfulnessResult(verdict, score, expl, passed, failed)


def _unknown(reason: str) -> FaithfulnessResult:
    return FaithfulnessResult(Verdict.UNKNOWN, 0.0, reason)


# ─────────────────────────────────────────────────────────────────────────────
# Base checker
# ─────────────────────────────────────────────────────────────────────────────

class PatternChecker(ABC):
    pattern_id: str

    def check(self, slow_code: str, model_output: str) -> FaithfulnessResult:
        ast_result = self._ast_check(slow_code, model_output)
        if ast_result and ast_result.verdict != Verdict.UNKNOWN:
            return ast_result
        return self._regex_check(slow_code, model_output)

    def _ast_check(self, slow_code: str, model_output: str) -> Optional[FaithfulnessResult]:
        return None

    @abstractmethod
    def _regex_check(self, slow_code: str, model_output: str) -> FaithfulnessResult:
        ...
