"""
semantic_redundancy.py
----------------------
SR — Semantic Redundancy checkers (SR-1 through SR-5).
"""

import re

from ._base import PatternChecker, _result
from ._ast_helpers import (
    _TRANSCENDENTAL,
    _calls_at_depth,
    _loop_stats,
)


class SR1Checker(PatternChecker):
    """SR-1: Loop-Invariant Computation — expensive call or expression hoisted outside loop.

    Two sub-forms:
      A) Function-call form: series_fn()/transcendental called once outside loop.
      B) Algebraic form: loop-invariant scalar multiplier factored out
         (sum computed in loop, multiply/combine done after loop).
    """
    pattern_id = "SR-1"

    def _ast_check(self, slow_code, model_output):
        slow_calls = _calls_at_depth(slow_code)
        out_calls  = _calls_at_depth(model_output)
        if slow_calls is None or out_calls is None:
            return None
        passed, failed = [], []

        stdlib = {"malloc", "calloc", "free", "memset", "memcpy", "memmove", "printf"}
        # Form A: user/transcendental calls that were inside slow's loop
        slow_in_loop = {n for n, d in slow_calls if d > 0 and n not in stdlib}
        out_in_loop  = {n for n, d in out_calls  if d > 0 and n not in stdlib}

        if slow_in_loop:
            # Check if in-loop calls are data-dependent (args contain array subscript [)
            # Data-dependent calls can't be hoisted — Form B (accumulator separation) applies.
            def _is_data_dependent(code, call_names):
                for name in call_names:
                    if re.search(r'\b' + re.escape(name) + r'\s*\([^)]*\[', code):
                        return True
                return False

            if _is_data_dependent(slow_code, slow_in_loop):
                # Form B: calls depend on loop variable — check accumulator separation
                multi_accum = len(re.findall(r'\b(?:sum|acc|total)\w*\s*[+*]?=\s*', model_output)) >= 3
                if multi_accum:
                    passed.append("algebraic form: multiple accumulators separate loop-variant calls")
                else:
                    passed.append("data-dependent calls correctly remain inside loop (cannot hoist)")
            else:
                still_inside = slow_in_loop & out_in_loop
                hoisted      = slow_in_loop - out_in_loop
                if hoisted:
                    passed.append(f"call(s) {sorted(hoisted)} hoisted out of loop")
                if still_inside:
                    failed.append(f"call(s) {sorted(still_inside)} still inside loop")
                if not still_inside:
                    passed.append("no expensive calls remain inside loop body")
        else:
            # Form B: algebraic — check work moved outside loop via accumulator pattern:
            # fast version accumulates in separate sums then combines after the loop
            out_loop_count = _loop_stats(model_output)
            has_post_loop_combine = bool(re.search(
                r'(?:for|while)\s*[^{]*\{[^{}]*\}[^;]*return\s+[^;]+[+\-*][^;]+;',
                model_output, re.DOTALL
            ))
            # Simpler heuristic: multiple scalar accumulators declared before loop
            multi_accum = len(re.findall(r'\b(?:sum|acc|total)\w*\s*=\s*0', model_output)) >= 2
            if multi_accum or has_post_loop_combine:
                passed.append("algebraic form: multiple accumulators / post-loop combination detected")
            else:
                passed.append("no function calls inside loop (computation restructured)")

        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        fns = "|".join(_TRANSCENDENTAL)
        # Check transcendental calls not inside loop
        in_loop = re.search(
            r'(?:for|while)\s*[^{]*\{[^}]*(?:' + fns + r')\s*\(',
            model_output, re.DOTALL
        )
        if in_loop:
            failed.append("transcendental call appears to be inside loop")
        else:
            passed.append("no transcendental call inside loop")
        # Algebraic form: return combines sums after loop
        if re.search(r'\breturn\b[^;]*[+\-][^;]*;', model_output):
            passed.append("post-loop combination in return statement")
        return _result(passed, failed)


class SR2Checker(PatternChecker):
    """SR-2: Expression Decomposition — compound expression broken into separate accumulators.

    Two sub-forms:
      A) Function-call form: loop-invariant function call decomposed out of compound expression.
      B) Algebraic form: monolithic loop body with temporaries (t1..tN) replaced by
         separate accumulator sums combined after the loop.
    """
    pattern_id = "SR-2"

    def _ast_check(self, slow_code, model_output):
        slow_calls = _calls_at_depth(slow_code) or []
        out_calls  = _calls_at_depth(model_output) or []
        slow_count_in = sum(1 for _, d in slow_calls if d > 0)
        out_count_in  = sum(1 for _, d in out_calls  if d > 0)
        passed, failed = [], []

        if slow_count_in > 0:
            # Form A: function call decomposition
            if out_count_in < slow_count_in:
                passed.append(f"calls inside loop reduced: {slow_count_in} → {out_count_in}")
            else:
                failed.append(f"calls inside loop not reduced ({out_count_in} vs slow {slow_count_in})")
        else:
            # Form B: algebraic decomposition — check temp variable count and post-loop combine
            slow_tmps = len(re.findall(r'\b(?:int|float|double)\s+t\d+\s*=', slow_code))
            out_tmps  = len(re.findall(r'\b(?:int|float|double)\s+t\d+\s*=', model_output))
            # Count any scalar temporaries inside loop body
            slow_in_loop_assigns = len(re.findall(
                r'for\s*\([^)]*\)\s*\{[^{}]*(?:int|float|double)\s+\w+\s*=',
                slow_code, re.DOTALL))
            out_in_loop_assigns = len(re.findall(
                r'for\s*\([^)]*\)\s*\{[^{}]*(?:int|float|double)\s+\w+\s*=',
                model_output, re.DOTALL))

            if slow_tmps > 0 and out_tmps < slow_tmps:
                passed.append(f"redundant temporaries eliminated: {slow_tmps} → {out_tmps}")
            elif out_in_loop_assigns < slow_in_loop_assigns:
                passed.append(f"in-loop assignments reduced: {slow_in_loop_assigns} → {out_in_loop_assigns}")
            else:
                passed.append("algebraic decomposition — loop body simplified")

            # Fast version should combine sums after loop (return with arithmetic)
            if re.search(r'\breturn\b[^;]*[+\-*][^;]+[+\-*][^;]*;', model_output):
                passed.append("post-loop algebraic combination in return")

        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_tmps = len(re.findall(r'\bt\d+\s*=', slow_code))
        out_tmps  = len(re.findall(r'\bt\d+\s*=', model_output))
        if slow_tmps > 0 and out_tmps < slow_tmps:
            passed.append(f"temporaries reduced: {slow_tmps} → {out_tmps}")
        elif re.search(r'(?:int|float|double)\s+\w+\s*=[^;]+;[^{]*for\s*\(', model_output, re.DOTALL):
            passed.append("scalar pre-computed before loop detected")
        else:
            passed.append("expression decomposed (no obvious temporaries to reduce)")
        return _result(passed, failed)


class SR3Checker(PatternChecker):
    """SR-3: Redundant Aggregation — O(n²) running sum replaced with O(n) incremental."""
    pattern_id = "SR-3"

    def _ast_check(self, slow_code, model_output):
        slow_stats = _loop_stats(slow_code)
        out_stats  = _loop_stats(model_output)
        if slow_stats is None or out_stats is None:
            return None
        passed, failed = [], []
        if slow_stats[1] >= 2 and out_stats[1] < slow_stats[1]:
            passed.append(f"loop nesting reduced: max depth {slow_stats[1]} → {out_stats[1]}")
        elif out_stats[1] >= slow_stats[1] and slow_stats[1] >= 2:
            failed.append(f"nested loops still present (max depth {out_stats[1]})")
        else:
            passed.append("single-pass loop structure (no nesting)")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_loops = len(re.findall(r'\bfor\s*\(', slow_code))
        out_loops  = len(re.findall(r'\bfor\s*\(', model_output))
        nested = bool(re.search(r'for\s*\([^)]*\)[^{]*\{[^}]*for\s*\(', model_output, re.DOTALL))
        if nested:
            failed.append("nested for-loop detected — O(n²) structure may remain")
        else:
            passed.append("no nested for-loop — likely single-pass")
        return _result(passed, failed)


class SR4Checker(PatternChecker):
    """SR-4: Loop-Invariant Config Call — config/setup function hoisted outside loop."""
    pattern_id = "SR-4"

    def _ast_check(self, slow_code, model_output):
        slow_calls = _calls_at_depth(slow_code) or []
        out_calls  = _calls_at_depth(model_output) or []
        stdlib = _TRANSCENDENTAL | {"malloc","calloc","free","memset","memcpy","memmove","printf"}
        slow_user_in = [(n, d) for n, d in slow_calls if n not in stdlib and d > 0]
        out_user_in  = [(n, d) for n, d in out_calls  if n not in stdlib and d > 0]
        passed, failed = [], []
        if len(out_user_in) < len(slow_user_in):
            passed.append(f"user function calls in loop reduced: {len(slow_user_in)} → {len(out_user_in)}")
        elif slow_user_in:
            failed.append(f"user function calls still in loop: {[n for n,_ in out_user_in]}")
        else:
            passed.append("no user function calls remain inside loop")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Look for a cached variable assigned from a function call before a loop
        if re.search(r'=\s*\w+\s*\([^)]*\)\s*;[^{]*for\s*\(', model_output, re.DOTALL):
            passed.append("function call result cached before loop")
        else:
            failed.append("no pre-loop function call caching detected")
        return _result(passed, failed)


class SR5Checker(PatternChecker):
    """SR-5: Division by Loop-Invariant — replaced with multiply-by-reciprocal."""
    pattern_id = "SR-5"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        has_div_in_loop = bool(re.search(
            r'for\s*\([^)]*\)\s*\{[^}]*/[^/=\n][^}]*\}', model_output, re.DOTALL
        ))
        has_inv = bool(re.search(r'\binv\b|\brecip\b|1\.0\s*/|1\s*/', model_output))
        slow_has_div = bool(re.search(r'/\s*\w+\s*\(', slow_code))
        if slow_has_div:
            if has_inv:
                passed.append("reciprocal precomputed (1.0 / ...) detected")
            else:
                failed.append("no reciprocal precomputation found")
            if has_div_in_loop:
                failed.append("division still present inside loop")
            else:
                passed.append("no division operator inside loop")
        else:
            passed.append("slow code has no obvious divisor to hoist")
        return _result(passed, failed)
