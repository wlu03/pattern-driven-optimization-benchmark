"""
human_style.py
--------------
HR — Human-Style Antipattern checkers (HR-1 through HR-5).
"""

import re

from ._base import PatternChecker, _result
from ._ast_helpers import (
    _if_stats,
    _loop_stats,
    _malloc_stats,
)


class HR1Checker(PatternChecker):
    """HR-1: Redundant Temp Arrays — heap arrays replaced with register variables."""
    pattern_id = "HR-1"

    def _ast_check(self, slow_code, model_output):
        slow_m = _malloc_stats(slow_code)
        out_m  = _malloc_stats(model_output)
        if slow_m is None or out_m is None:
            return None
        passed, failed = [], []
        slow_total = slow_m[0] + slow_m[1]
        out_total  = out_m[0] + out_m[1]
        if slow_total > 0 and out_total < slow_total:
            passed.append(f"malloc calls reduced: {slow_total} → {out_total}")
        elif slow_total > 0 and out_total >= slow_total:
            failed.append(f"malloc calls not reduced (out={out_total}, slow={slow_total})")
        else:
            passed.append("no heap allocation (register/stack variables used)")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_mallocs = len(re.findall(r'\bmalloc\s*\(', slow_code))
        out_mallocs  = len(re.findall(r'\bmalloc\s*\(', model_output))
        if slow_mallocs > 0 and out_mallocs < slow_mallocs:
            passed.append(f"malloc reduced: {slow_mallocs} → {out_mallocs}")
        elif slow_mallocs > 0:
            failed.append("malloc calls not eliminated")
        else:
            passed.append("no malloc in slow code")
        return _result(passed, failed)


class HR2Checker(PatternChecker):
    """HR-2: Copy-Paste Loop Fusion — multiple loops fused into one."""
    pattern_id = "HR-2"

    def _ast_check(self, slow_code, model_output):
        slow_s = _loop_stats(slow_code)
        out_s  = _loop_stats(model_output)
        if slow_s is None or out_s is None:
            return None
        passed, failed = [], []
        if out_s[0] < slow_s[0]:
            passed.append(f"loop count reduced: {slow_s[0]} → {out_s[0]} (loops fused)")
        else:
            failed.append(f"loop count not reduced (out={out_s[0]}, slow={slow_s[0]})")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_loops = len(re.findall(r'\bfor\s*\(', slow_code))
        out_loops  = len(re.findall(r'\bfor\s*\(', model_output))
        if out_loops < slow_loops:
            passed.append(f"for-loop count reduced: {slow_loops} → {out_loops}")
        else:
            failed.append(f"for-loop count not reduced ({out_loops} vs slow {slow_loops})")
        return _result(passed, failed)


class HR3Checker(PatternChecker):
    """HR-3: Dead Debug Code — printf/debug statements removed."""
    pattern_id = "HR-3"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_debug = len(re.findall(r'\bprintf\s*\(|\bfprintf\s*\(|\bassert\s*\(', slow_code))
        out_debug  = len(re.findall(r'\bprintf\s*\(|\bfprintf\s*\(|\bassert\s*\(', model_output))
        if slow_debug > 0 and out_debug < slow_debug:
            passed.append(f"debug calls reduced: {slow_debug} → {out_debug}")
        elif slow_debug > 0 and out_debug >= slow_debug:
            failed.append("debug/printf calls not removed")
        else:
            passed.append("no debug calls in slow code")
        return _result(passed, failed)


class HR4Checker(PatternChecker):
    """HR-4: Defensive Checks in Hot Loop — NULL/bounds guards moved outside loop."""
    pattern_id = "HR-4"

    def _ast_check(self, slow_code, model_output):
        slow_if = _if_stats(slow_code)
        out_if  = _if_stats(model_output)
        if slow_if is None or out_if is None:
            return None
        passed, failed = [], []
        if out_if[0] < slow_if[0]:
            passed.append(f"in-loop conditionals reduced: {slow_if[0]} → {out_if[0]}")
        elif slow_if[0] > 0:
            failed.append(f"defensive checks still inside loop ({out_if[0]} branches)")
        if out_if[1] >= 1:
            passed.append("guard check present outside loop (correct position)")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Form A: Null/bounds check before loop
        has_pre_guard = bool(re.search(
            r'(?:if\s*\([^)]*(?:NULL|null|== 0|<= 0|!= NULL)[^)]*\)[^{]*\{[^}]*return[^}]*\}'
            r'|if\s*\([^)]*NULL[^)]*\)\s*return)',
            model_output
        ))
        if has_pre_guard:
            passed.append("NULL/bounds guard before loop detected")
        slow_in_loop_ifs = len(re.findall(
            r'for\s*\([^)]*\)\s*\{[^}]*\bif\s*\([^)]*(?:NULL|== 0|<= 0)[^)]*\)[^}]*\}',
            slow_code, re.DOTALL
        ))
        out_in_loop_ifs = len(re.findall(
            r'for\s*\([^)]*\)\s*\{[^}]*\bif\s*\([^)]*(?:NULL|== 0|<= 0)[^)]*\)[^}]*\}',
            model_output, re.DOTALL
        ))
        if slow_in_loop_ifs > 0 and out_in_loop_ifs == 0:
            passed.append("defensive checks removed from loop body")
        elif slow_in_loop_ifs > 0:
            failed.append("defensive checks still inside loop")
        # Form B: Slow calls a noinline check helper per iteration; fast skips it
        if not passed and not failed:
            # Check if slow calls a user function inside loop that fast doesn't
            slow_user_calls = set(re.findall(r'\b(hr4_\w+|check_\w+)\s*\(', slow_code))
            out_user_calls = set(re.findall(r'\b(hr4_\w+|check_\w+)\s*\(', model_output))
            eliminated = slow_user_calls - out_user_calls
            if eliminated:
                passed.append(f"check function(s) {sorted(eliminated)} eliminated from fast path")
        return _result(passed, failed)


class HR5Checker(PatternChecker):
    """HR-5: Dead Conditional Code — always-true/dead if-checks removed from loop."""
    pattern_id = "HR-5"

    def _ast_check(self, slow_code, model_output):
        slow_if = _if_stats(slow_code)
        out_if  = _if_stats(model_output)
        if slow_if is None or out_if is None:
            return None
        passed, failed = [], []
        if slow_if[0] > 0 and out_if[0] < slow_if[0]:
            passed.append(f"dead conditionals in loop removed: {slow_if[0]} → {out_if[0]}")
        elif slow_if[0] > 0 and out_if[0] >= slow_if[0]:
            failed.append(f"dead conditionals not removed from loop ({out_if[0]} remain)")
        else:
            passed.append("no dead conditionals in loop")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_ifs = len(re.findall(r'\bif\s*\(', slow_code))
        out_ifs  = len(re.findall(r'\bif\s*\(', model_output))
        if slow_ifs > 0 and out_ifs < slow_ifs:
            passed.append(f"if-statements reduced: {slow_ifs} → {out_ifs} (dead code removed)")
        elif slow_ifs > 0:
            failed.append(f"if-statements not reduced ({out_ifs} vs slow {slow_ifs})")
        else:
            passed.append("no dead conditionals to remove")
        return _result(passed, failed)
