"""
memory_io.py
------------
MI — Memory / IO checkers (MI-1 through MI-4).
"""

import re

from ._base import PatternChecker, _result
from ._ast_helpers import (
    _OuterLoopVar,
    _loop_stats,
    _malloc_stats,
    _parse,
)


class MI1Checker(PatternChecker):
    """MI-1: Allocation in Loop — malloc replaced with sliding window (no alloc)."""
    pattern_id = "MI-1"

    def _ast_check(self, slow_code, model_output):
        slow_m = _malloc_stats(slow_code)
        out_m  = _malloc_stats(model_output)
        if slow_m is None or out_m is None:
            return None
        passed, failed = [], []
        if slow_m[0] > 0 and out_m[0] == 0:
            passed.append("malloc eliminated from loop body")
        elif out_m[0] > 0:
            failed.append(f"malloc still inside loop ({out_m[0]} calls)")
        else:
            passed.append("no malloc in loop")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_m_in = bool(re.search(
            r'for\s*\([^)]*\)\s*\{[^}]*\bmalloc\s*\(', slow_code, re.DOTALL))
        out_m_in  = bool(re.search(
            r'for\s*\([^)]*\)\s*\{[^}]*\bmalloc\s*\(', model_output, re.DOTALL))
        if slow_m_in and not out_m_in:
            passed.append("malloc removed from loop body (sliding window)")
        elif out_m_in:
            failed.append("malloc still inside loop")
        else:
            passed.append("no in-loop malloc")
        # Sliding window: adds/removes single element
        if re.search(r'sum\s*[+-]=\s*\w+\[\w+[^]]*\]', model_output):
            passed.append("sliding window update detected (add/remove element)")
        return _result(passed, failed)


class MI2Checker(PatternChecker):
    """MI-2: Redundant Multi-Pass / Redundant zeroing — reduced to single pass.

    Two sub-forms:
      A) Multi-pass with heap intermediates: malloc+3-pass → single pass (no malloc).
      B) Redundant memset: memset before a loop that overwrites every element → remove memset.
    """
    pattern_id = "MI-2"

    def _ast_check(self, slow_code, model_output):
        slow_m = _malloc_stats(slow_code)
        out_m  = _malloc_stats(model_output)
        slow_l = _loop_stats(slow_code)
        out_l  = _loop_stats(model_output)
        if None in (slow_m, out_m, slow_l, out_l):
            return None
        passed, failed = [], []
        slow_total_m = slow_m[0] + slow_m[1]
        out_total_m  = out_m[0] + out_m[1]
        if slow_total_m > 0 and out_total_m < slow_total_m:
            passed.append(f"heap allocations reduced: {slow_total_m} → {out_total_m}")
        elif slow_total_m > 0:
            failed.append("intermediate heap arrays not eliminated")
        if out_l[0] < slow_l[0]:
            passed.append(f"loop count reduced: {slow_l[0]} → {out_l[0]} (passes fused)")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_mallocs = len(re.findall(r'\bmalloc\s*\(', slow_code))
        out_mallocs  = len(re.findall(r'\bmalloc\s*\(', model_output))
        slow_loops   = len(re.findall(r'\bfor\s*\(', slow_code))
        out_loops    = len(re.findall(r'\bfor\s*\(', model_output))
        slow_memsets = len(re.findall(r'\bmemset\s*\(', slow_code))
        out_memsets  = len(re.findall(r'\bmemset\s*\(', model_output))

        any_check = False

        # Form A: malloc reduction
        if slow_mallocs > 0:
            any_check = True
            if out_mallocs < slow_mallocs:
                passed.append(f"malloc reduced: {slow_mallocs} → {out_mallocs}")
            else:
                failed.append("intermediate mallocs not removed")

        # Form B: redundant memset removed
        if slow_memsets > 0:
            any_check = True
            if out_memsets < slow_memsets:
                passed.append(f"redundant memset removed: {slow_memsets} → {out_memsets}")
            else:
                failed.append("redundant memset not removed")

        # Loop count reduction (both forms)
        if slow_loops > 0:
            any_check = True
            if out_loops <= slow_loops:
                passed.append(f"loop count not increased ({out_loops} vs slow {slow_loops})")
            else:
                failed.append(f"loop count increased ({out_loops} vs slow {slow_loops})")

        if not any_check:
            passed.append("no malloc or memset in slow code — single-pass assumed")

        return _result(passed, failed)


class MI3Checker(PatternChecker):
    """MI-3: Heap Allocation in Hot Loop — replaced with stack/pre-allocated buffer."""
    pattern_id = "MI-3"

    def _ast_check(self, slow_code, model_output):
        return MI1Checker()._ast_check(slow_code, model_output)  # same structural check

    def _regex_check(self, slow_code, model_output):
        return MI1Checker()._regex_check(slow_code, model_output)


class MI4Checker(PatternChecker):
    """MI-4: Cache-Unfriendly Access — column-major → row-major loop order."""
    pattern_id = "MI-4"

    def _ast_check(self, slow_code, model_output):
        slow_ast = _parse(slow_code)
        out_ast  = _parse(model_output)
        if slow_ast is None or out_ast is None:
            return None
        slow_v = _OuterLoopVar(); slow_v.visit(slow_ast)
        out_v  = _OuterLoopVar(); out_v.visit(out_ast)
        passed, failed = [], []
        if slow_v.outer_vars and out_v.outer_vars:
            s_outer = slow_v.outer_vars[0]
            # Check primary outer loop first, then any secondary loop (for COMP variants
            # where the traversal loop is not the first loop in the function)
            swapped = any(v != s_outer for v in out_v.outer_vars)
            if swapped:
                new_outer = next(v for v in out_v.outer_vars if v != s_outer)
                passed.append(f"outer loop variable changed: '{s_outer}' → '{new_outer}' (loop order swapped)")
            else:
                failed.append(f"outer loop variable unchanged ('{out_v.outer_vars[0]}') — loop order may not be swapped")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Slow: outer=j, inner=i (column-major: mat[i*cols + j])
        # Fast: outer=i, inner=j (row-major: mat[i*cols + j])
        slow_outer_j = bool(re.search(r'for\s*\(\s*int\s+j\s*=', slow_code))
        out_outer_i  = bool(re.search(r'for\s*\(\s*int\s+i\s*=', model_output))
        if slow_outer_j and out_outer_i:
            passed.append("loop order swapped from column-major (j outer) to row-major (i outer)")
        elif slow_outer_j:
            failed.append("outer loop still iterates over j (column-major not fixed)")
        else:
            passed.append("loop order check inconclusive (variable names unclear)")
        return _result(passed, failed)
