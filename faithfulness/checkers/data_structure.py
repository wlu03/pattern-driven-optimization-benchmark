"""
data_structure.py
-----------------
DS — Data Structure Choice checkers (DS-1 through DS-4).
"""

import re

from ._base import PatternChecker, _result
from ._ast_helpers import (
    _StructParamChecker,
    _malloc_stats,
    _parse,
)


class DS1Checker(PatternChecker):
    """DS-1: Linear Search → Hash Table — O(n) lookup replaced with O(1)."""
    pattern_id = "DS-1"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Hash table: uses modulo for bucket indexing
        # Hash: modulo (%), bitwise AND mask (& N), or hash/bucket naming
        has_hash = bool(re.search(r'\s%\s*\w+|&\s*\d+|\bHASH\b|\bhash\b|\bbucket\b|\btable\b|\bht\b', model_output))
        # Slow code has linear search (nested loop or sequential scan)
        slow_nested = bool(re.search(r'for[^}]*\{[^}]*for\s*\(', slow_code, re.DOTALL))
        if has_hash:
            passed.append("hash/modulo indexing detected (hash table pattern)")
        else:
            failed.append("no hash table pattern detected")
        if slow_nested and not re.search(r'for[^}]*\{[^}]*for\s*\(', model_output, re.DOTALL):
            passed.append("nested loop (linear search) eliminated")
        return _result(passed, failed)


class DS2Checker(PatternChecker):
    """DS-2: Repeated Allocation — malloc/free moved outside loop."""
    pattern_id = "DS-2"

    def _ast_check(self, slow_code, model_output):
        slow_m = _malloc_stats(slow_code)
        out_m  = _malloc_stats(model_output)
        if slow_m is None or out_m is None:
            return None
        passed, failed = [], []
        if slow_m[0] > 0 and out_m[0] == 0:
            passed.append("malloc moved outside loop (no malloc inside loop)")
        elif slow_m[0] > 0 and out_m[0] > 0:
            failed.append(f"malloc still inside loop ({out_m[0]} calls)")
        else:
            passed.append("no malloc inside loop")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_m_in = bool(re.search(
            r'for\s*\([^)]*\)\s*\{[^}]*\bmalloc\s*\(', slow_code, re.DOTALL))
        out_m_in  = bool(re.search(
            r'for\s*\([^)]*\)\s*\{[^}]*\bmalloc\s*\(', model_output, re.DOTALL))
        if slow_m_in and not out_m_in:
            passed.append("malloc hoisted outside loop")
        elif out_m_in:
            failed.append("malloc still inside loop")
        else:
            passed.append("no in-loop malloc detected")
        return _result(passed, failed)


class DS3Checker(PatternChecker):
    """DS-3: Unnecessary Copy — redundant memcpy/array copy eliminated."""
    pattern_id = "DS-3"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_copies = len(re.findall(r'\bmemcpy\s*\(|\bfor[^}]*\w+\[i\]\s*=\s*\w+\[i\]', slow_code))
        out_copies  = len(re.findall(r'\bmemcpy\s*\(|\bfor[^}]*\w+\[i\]\s*=\s*\w+\[i\]', model_output))
        if slow_copies > 0 and out_copies < slow_copies:
            passed.append(f"copy operations reduced: {slow_copies} → {out_copies}")
        elif slow_copies > 0:
            failed.append("unnecessary copy not eliminated")
        else:
            passed.append("no obvious copy in slow code")
        return _result(passed, failed)


class DS4Checker(PatternChecker):
    """DS-4: AoS → SoA — struct-pointer parameter replaced with separate arrays."""
    pattern_id = "DS-4"

    def _ast_check(self, slow_code, model_output):
        slow_v = _StructParamChecker()
        out_v  = _StructParamChecker()
        slow_ast = _parse(slow_code)
        out_ast  = _parse(model_output)
        if slow_ast is None or out_ast is None:
            return None
        slow_v.visit(slow_ast)
        out_v.visit(out_ast)
        passed, failed = [], []
        if slow_v.has_struct_param and not out_v.has_struct_param:
            passed.append("struct parameter replaced with scalar/array parameters (AoS→SoA)")
        elif out_v.has_struct_param:
            failed.append("struct parameter still present in function signature")
        else:
            passed.append("no struct parameter in output (SoA layout)")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        has_struct_param_slow = bool(re.search(r'\bstruct\b\s+\w+\s*\*', slow_code))
        has_struct_param_out  = bool(re.search(r'\bstruct\b\s+\w+\s*\*', model_output))
        if has_struct_param_slow and not has_struct_param_out:
            passed.append("struct pointer parameter eliminated (AoS→SoA)")
        elif has_struct_param_out:
            failed.append("struct pointer still in function signature")
        else:
            passed.append("no struct pointer in output")
        return _result(passed, failed)
