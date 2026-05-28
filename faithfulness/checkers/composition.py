"""
composition.py
--------------
COMP — Composed pattern checker that recursively dispatches to sub-checkers.

To avoid a circular import (the package `__init__` imports this module while
also building the `CHECKERS` registry), we look up `CHECKERS` lazily at call
time from the parent package.
"""

import re

from ._base import (
    FaithfulnessResult,
    PatternChecker,
    Verdict,
)


class COMPChecker(PatternChecker):
    """COMP: Multiple overlapping patterns — runs sub-checkers for each constituent."""
    pattern_id = "COMP"

    def check(self, slow_code: str, model_output: str,
              composition: list[str] | None = None) -> FaithfulnessResult:
        """
        Args:
            composition: list of constituent pattern IDs, e.g. ["SR-2", "HR-1"].
                         If None, falls back to a generic battery.
                         Pass metadata["composition"] from the variant's metadata.json.
        """
        if not composition:
            # Generic fallback battery when composition unknown
            return self._generic_check(slow_code, model_output)

        # Lazy import to avoid circular dependency: COMPChecker is itself one of
        # the entries in CHECKERS, so we cannot import CHECKERS at module load.
        from . import CHECKERS  # noqa: PLC0415

        passed, failed = [], []
        for pid in composition:
            checker = CHECKERS.get(pid)
            if checker is None:
                passed.append(f"{pid}: no checker (skipped)")
                continue
            result = checker.check(slow_code, model_output)
            if result.verdict == Verdict.FAITHFUL:
                passed.append(f"{pid}: faithful ({result.explanation})")
            elif result.verdict == Verdict.PARTIAL:
                passed.append(f"{pid}: partial ({result.explanation})")
                failed.append(f"{pid}: not fully faithful")
            else:
                failed.append(f"{pid}: {result.verdict} — {result.explanation}")

        score = len(passed) / max(len(passed) + len(failed), 1)
        n_faithful = sum(1 for p in passed if ": faithful" in p or ": partial" in p)
        if n_faithful >= max(1, len(composition) - 1):
            verdict = Verdict.FAITHFUL if score >= 0.75 else Verdict.PARTIAL
        elif n_faithful == 0:
            verdict = Verdict.UNFAITHFUL
        else:
            verdict = Verdict.PARTIAL
        expl = f"{n_faithful}/{len(composition)} constituent pattern fixes applied"
        return FaithfulnessResult(verdict, score, expl, passed, failed)

    def _generic_check(self, slow_code: str, model_output: str) -> FaithfulnessResult:
        """Fallback when composition metadata is unavailable."""
        sub_checks = [
            ("no recursion",    lambda: not bool(re.search(r'\b(\w+)\s*\([^)]*\)[^{]*\{[^}]*\1\s*\(', model_output, re.DOTALL))),
            ("if hoisted",      lambda: not bool(re.search(r'for[^{]*\{[^}]*\bif\b[^}]*mode[^}]*\}', model_output, re.DOTALL))),
            ("no null in loop", lambda: not bool(re.search(r'for[^{]*\{[^}]*NULL[^}]*\}', model_output, re.DOTALL))),
            ("no struct param", lambda: not bool(re.search(r'\bstruct\b\s+\w+\s*\*', model_output))
                                        or not bool(re.search(r'\bstruct\b\s+\w+\s*\*', slow_code))),
        ]
        passed, failed = [], []
        for name, fn in sub_checks:
            try:
                (passed if fn() else failed).append(name)
            except Exception:
                pass
        score = len(passed) / max(len(passed) + len(failed), 1)
        verdict = Verdict.FAITHFUL if score >= 0.75 else (Verdict.PARTIAL if score > 0 else Verdict.UNFAITHFUL)
        return FaithfulnessResult(verdict, score, f"{len(passed)}/{len(passed)+len(failed)} generic checks passed", passed, failed)

    def _regex_check(self, slow_code, model_output):
        return self._generic_check(slow_code, model_output)
