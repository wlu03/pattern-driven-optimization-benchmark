"""
control_flow.py
---------------
CF — Control Flow checkers (CF-1 through CF-4).
"""

import re

from ._base import PatternChecker, _result
from ._ast_helpers import (
    _TRANSCENDENTAL,
    _calls_at_depth,
    _if_stats,
)


class CF1Checker(PatternChecker):
    """CF-1: Data-Uniform Batch Dispatch — mode/dispatch if hoisted outside loop."""
    pattern_id = "CF-1"

    def _ast_check(self, slow_code, model_output):
        slow_if = _if_stats(slow_code)
        out_if  = _if_stats(model_output)
        if slow_if is None or out_if is None:
            return None
        passed, failed = [], []
        if slow_if[0] > 0 and out_if[0] == 0:
            passed.append("all conditionals moved outside loop body")
        elif out_if[0] < slow_if[0]:
            passed.append(f"conditionals in loop reduced: {slow_if[0]} → {out_if[0]}")
        elif slow_if[0] > 0:
            failed.append(f"conditionals still inside loop ({out_if[0]} branches at depth>0)")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Count if-statements inside loops in slow vs fast (crude regex estimate)
        def _in_loop_ifs(code):
            count = 0
            in_loop = False
            for line in code.splitlines():
                s = line.strip()
                if re.match(r'for\s*\(|while\s*\(', s):
                    in_loop = True
                if in_loop and re.match(r'if\s*\(', s):
                    count += 1
            return count
        slow_ifs = _in_loop_ifs(slow_code)
        fast_ifs  = _in_loop_ifs(model_output)
        # Fast version should have if BEFORE loop, then separate loops per branch
        if re.search(r'if\s*\([^)]*mode[^)]*\)[^{]*\{[^}]*for\s*\(', model_output, re.DOTALL):
            passed.append("dispatch conditional precedes loop (hoisted)")
        elif re.search(r'if\s*\(.*\)\s*\{', model_output) and re.search(r'for\s*\(', model_output):
            passed.append("if-statement and loop both present (likely restructured)")
        elif fast_ifs < slow_ifs:
            passed.append(f"in-loop conditionals reduced: {slow_ifs} → {fast_ifs}")
        elif re.search(r'\?[^:]+:', model_output) and fast_ifs == 0 and re.search(r'for\s*\(', model_output):
            # Ternary dispatch hoisted before loop — equivalent to if hoisting
            passed.append("ternary dispatch hoisted outside loop body")
        else:
            failed.append("no hoisted dispatch conditional detected")
        return _result(passed, failed)


class CF2Checker(PatternChecker):
    """CF-2: Hot/Cold Path Separation — 99% path loop freed from branch overhead."""
    pattern_id = "CF-2"

    def _ast_check(self, slow_code, model_output):
        slow_if = _if_stats(slow_code)
        out_if  = _if_stats(model_output)
        if slow_if is None or out_if is None:
            return None
        passed, failed = [], []
        if out_if[0] < slow_if[0]:
            passed.append(f"branches inside loop reduced: {slow_if[0]} → {out_if[0]}")
        elif slow_if[0] > 0 and out_if[0] >= slow_if[0]:
            failed.append("branch count inside loop not reduced")
        else:
            passed.append("minimal branching in loop body")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_in_loop_calls = len(re.findall(
            r'for\s*\([^)]*\)[^{]*\{[^}]*\w+\s*\([^}]*\}', slow_code, re.DOTALL))
        # Fast version should have the hot loop as a simple inner loop
        simple_loop = bool(re.search(
            r'for\s*\([^)]*\)\s*\{[^{}]*\}', model_output
        ))
        if simple_loop:
            passed.append("simple inner loop without nested calls detected")
        else:
            failed.append("no simple inner loop found")
        return _result(passed, failed)


class CF3Checker(PatternChecker):
    """CF-3: Vectorization-Hostile Conditional — noinline guard function eliminated, loop simplified.

    Slow: calls a noinline function that wraps computation with an always-true conditional.
    Fast: inlines the computation directly, removing the function call and the conditional.
    """
    pattern_id = "CF-3"

    def _ast_check(self, slow_code, model_output):
        slow_calls = _calls_at_depth(slow_code)
        out_calls  = _calls_at_depth(model_output)
        if slow_calls is None or out_calls is None:
            return None
        stdlib = _TRANSCENDENTAL | {"malloc","calloc","free","memset","memcpy","memmove","printf"}
        slow_user_in = [(n, d) for n, d in slow_calls if n not in stdlib and d > 0]
        out_user_in  = [(n, d) for n, d in out_calls  if n not in stdlib and d > 0]
        passed, failed = [], []
        if slow_user_in and not out_user_in:
            passed.append(f"noinline guard function {[n for n,_ in slow_user_in]} eliminated from loop")
        elif slow_user_in and out_user_in:
            failed.append(f"user function call still in loop: {[n for n,_ in out_user_in]}")
        # No conditional in fast loop
        out_if = _if_stats(model_output)
        if out_if and out_if[0] == 0:
            passed.append("no conditional branch inside loop (guard eliminated)")
        elif out_if and out_if[0] > 0:
            failed.append("conditional branch still inside loop")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Slow calls a noinline function per element; fast should not
        slow_has_noinline_call = bool(re.search(r'noinline', slow_code))
        out_has_if = bool(re.search(r'\bif\s*\(', model_output))
        slow_has_user_call_in_loop = bool(re.search(
            r'for[^{]*\{[^}]*\w+_v\d+\s*\(', slow_code, re.DOTALL))
        out_has_user_call_in_loop = bool(re.search(
            r'for[^{]*\{[^}]*\w+_v\d+\s*\(', model_output, re.DOTALL))
        if slow_has_user_call_in_loop and not out_has_user_call_in_loop:
            passed.append("noinline function call eliminated from loop")
        elif slow_has_noinline_call and not out_has_if:
            passed.append("no conditional branch in output loop (guard removed)")
        else:
            failed.append("conditional in loop not removed")
        if not out_has_if:
            passed.append("no if-statement in output (computation unconditional)")
        return _result(passed, failed)


class CF4Checker(PatternChecker):
    """CF-4: Function Pointer Dispatch — indirect call replaced with direct calls."""
    pattern_id = "CF-4"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Function pointer pattern: (*fp)(...) or fp(...)
        has_fptr_slow = bool(re.search(r'\(\*\w+\)\s*\(', slow_code))
        has_fptr_out  = bool(re.search(r'\(\*\w+\)\s*\(', model_output))
        if has_fptr_slow and not has_fptr_out:
            passed.append("function pointer call eliminated")
        elif has_fptr_out:
            failed.append("function pointer call still present")
        else:
            # Check for void* fn pointer pattern
            has_void_fptr = bool(re.search(r'\bvoid\s*\*\s*\w+\b|\bfn_ptr\b|\bdispatch\b', slow_code))
            if has_void_fptr:
                passed.append("possible function pointer dispatch restructured")
            else:
                passed.append("no function pointer detected in slow code")
        return _result(passed, failed)
