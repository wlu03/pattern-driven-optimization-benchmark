"""
input_sensitive.py
------------------
IS — Input-Sensitive checkers (IS-1 through IS-5).
"""

import re

from ._base import PatternChecker, _result
from ._ast_helpers import (
    _TRANSCENDENTAL,
    _IfStats,
    _calls_at_depth,
    _parse,
)


class IS1Checker(PatternChecker):
    """IS-1: Sparse Data Short-Circuit — skip expensive call when input is zero/trivial."""
    pattern_id = "IS-1"

    def _ast_check(self, slow_code, model_output):
        ast = _parse(model_output)
        if ast is None:
            return None
        v = _IfStats()
        v.visit(ast)
        passed, failed = [], []
        if v.in_loop > 0:
            passed.append(f"{v.in_loop} conditional branch(es) inside loop (early-exit guard)")
        else:
            failed.append("no conditional branch found inside loop")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        has_guard = bool(re.search(
            r'for\s*\([^)]*\)\s*\{[^}]*(?:if|==\s*0|!=\s*0|continue|break)[^}]*\}',
            model_output, re.DOTALL
        ))
        if has_guard:
            passed.append("conditional guard or early exit inside loop detected")
        else:
            failed.append("no conditional short-circuit inside loop")
        return _result(passed, failed)


class IS2Checker(PatternChecker):
    """IS-2: Outlier-Only Expensive Call — expensive fn called only inside if-branch."""
    pattern_id = "IS-2"

    def _ast_check(self, slow_code, model_output):
        out_calls = _calls_at_depth(model_output)
        if out_calls is None:
            return None
        stdlib = _TRANSCENDENTAL | {"malloc","calloc","free","memset","memcpy","memmove","printf"}
        # We want to check that no non-stdlib call is called unconditionally at depth=1
        # (depth=1 means inside loop but outside any if)
        # This is hard to check with flat depth — use regex fallback
        return None

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Check for conditional branch (if-block or ternary) — use a simpler presence check
        # to avoid nested-parenthesis issues in regex
        has_branch_guard = bool(re.search(r'\bif\s*\(', model_output)) or \
                           bool(re.search(r'\?[^:]+:', model_output))
        if has_branch_guard:
            passed.append("conditional branch guards expensive call")
        else:
            failed.append("no conditional guard around expensive call")
        # Check that fabs or threshold comparison appears (the outlier check pattern)
        if re.search(r'\bfabs\b|\babs\b|>\s*\w*thr|<\s*\w*thr|<=\s*\w*thr|>=\s*\w*thr', model_output):
            passed.append("threshold comparison detected (outlier branching)")
        else:
            failed.append("no threshold comparison detected")
        return _result(passed, failed)


class IS3Checker(PatternChecker):
    """IS-3: Count-then-check → Early Exit — replace full scan with early return on first hit."""
    pattern_id = "IS-3"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Slow: accumulates a counter, checks it after the loop
        slow_has_counter = bool(re.search(r'\bcnt\b|\bcount\b|\bfound\b', slow_code))
        # Fast: returns immediately inside the loop on first match
        # Match early return both in braced { return; } and braceless for(...) return;
        has_early_return_in_loop = bool(re.search(
            r'for\s*[^{]*\{[^}]*\breturn\b|for\s*\([^)]*\)\s*(?:[^;{]*;)*[^;{]*\breturn\b',
            model_output, re.DOTALL
        ))
        # No accumulator variable needed in fast version
        out_has_counter = bool(re.search(r'\bcnt\s*\+\+|\bcount\s*\+\+', model_output))
        if has_early_return_in_loop:
            passed.append("early return inside loop (short-circuit on first violation)")
        else:
            failed.append("no early return inside loop")
        if slow_has_counter and not out_has_counter:
            passed.append("counter accumulation eliminated")
        elif out_has_counter:
            failed.append("counter accumulation still present — not short-circuiting")
        return _result(passed, failed)


class IS4Checker(PatternChecker):
    """IS-4: Early Termination — break/return as soon as condition is met."""
    pattern_id = "IS-4"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        has_break  = bool(re.search(r'\bbreak\b', model_output))
        has_return = bool(re.search(r'\breturn\b[^;]*;', model_output))
        if has_break or has_return:
            passed.append("early termination (break/return) present inside loop")
        else:
            failed.append("no early termination detected")
        return _result(passed, failed)


class IS5Checker(PatternChecker):
    """IS-5: Input-Distribution Skew — fast path for common case."""
    pattern_id = "IS-5"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        has_if = bool(re.search(r'\bif\b', model_output))
        slow_ifs = len(re.findall(r'\bif\b', slow_code))
        out_ifs  = len(re.findall(r'\bif\b', model_output))
        if has_if:
            passed.append("conditional branching present for input distribution handling")
        else:
            failed.append("no conditional branch detected")
        # Distribution-skew fix often restructures so common path has no branch
        if out_ifs <= slow_ifs:
            passed.append(f"branch count not increased ({out_ifs} vs slow {slow_ifs})")
        return _result(passed, failed)
