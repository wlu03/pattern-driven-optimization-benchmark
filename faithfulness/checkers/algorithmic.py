"""
algorithmic.py
--------------
AL — Algorithmic Inefficiency checkers (AL-1 through AL-4).
"""

import re

from ._base import PatternChecker, _result
from ._ast_helpers import (
    _ArrayDeclCount,
    _RecursionChecker,
    _calls_at_depth,
    _loop_stats,
    _parse,
)


class AL1Checker(PatternChecker):
    """AL-1: Brute Force → DP — recursion replaced with iterative DP."""
    pattern_id = "AL-1"

    def _ast_check(self, slow_code, model_output):
        slow_r = _RecursionChecker()
        out_r  = _RecursionChecker()
        slow_a = _ArrayDeclCount()
        out_a  = _ArrayDeclCount()
        slow_ast = _parse(slow_code)
        out_ast  = _parse(model_output)
        if slow_ast is None or out_ast is None:
            return None
        slow_r.visit(slow_ast); slow_a.visit(slow_ast)
        out_r.visit(out_ast);   out_a.visit(out_ast)
        passed, failed = [], []
        if slow_r.recursive_calls > 0 and out_r.recursive_calls == 0:
            passed.append("recursion eliminated")
        elif out_r.recursive_calls > 0:
            failed.append(f"recursive calls still present ({out_r.recursive_calls})")
        # DP table may be a local array OR heap-allocated via calloc/malloc;
        # O(1) iterative rolling variables (a,b or a,b,c) are also valid DP.
        out_calls = _calls_at_depth(model_output) or []
        has_calloc = any(n in ("calloc", "malloc") for n, _ in out_calls)
        out_loop_stats = _loop_stats(model_output)
        has_loop = out_loop_stats is not None and out_loop_stats[0] > 0
        if out_a.count > slow_a.count or has_calloc:
            passed.append("DP array introduced (local array or calloc)")
        elif has_loop and out_r.recursive_calls == 0:
            passed.append("iterative rolling-variable DP (O(1) space)")
        elif out_a.count == 0 and not has_calloc and slow_r.recursive_calls > 0:
            failed.append("no DP array found — memoization missing")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_rec = bool(re.search(r'\b(\w+)\s*\([^)]*\)[^{]*\{[^}]*\1\s*\(', slow_code, re.DOTALL))
        out_rec  = bool(re.search(r'\b(\w+)\s*\([^)]*\)[^{]*\{[^}]*\1\s*\(', model_output, re.DOTALL))
        has_dp_array = bool(re.search(r'\b(?:dp|memo|cache|tab)\s*[\[\(]', model_output))
        if slow_rec and not out_rec:
            passed.append("recursion replaced with iterative approach")
        elif out_rec:
            failed.append("recursive calls still present")
        if has_dp_array:
            passed.append("DP/memo array detected")
        elif slow_rec:
            failed.append("no DP/memo table found")
        return _result(passed, failed)


class AL2Checker(PatternChecker):
    """AL-2: Repeated Sort → Binary Search + Insertion."""
    pattern_id = "AL-2"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_sorts = len(re.findall(r'\bqsort\s*\(|\bsort\s*\(', slow_code))
        out_sorts  = len(re.findall(r'\bqsort\s*\(|\bsort\s*\(', model_output))
        has_bsearch = bool(re.search(r'\bbsearch\b|\bbinary.search\b', model_output, re.IGNORECASE))
        has_memmove = bool(re.search(r'\bmemmove\s*\(', model_output))
        if slow_sorts > 0 and out_sorts < slow_sorts:
            passed.append(f"sort calls reduced: {slow_sorts} → {out_sorts}")
        elif slow_sorts > 0:
            failed.append("sort call not eliminated")
        if has_bsearch or has_memmove:
            passed.append("binary search / memmove insertion detected")
        elif slow_sorts > 0:
            failed.append("no binary search or memmove found")
        return _result(passed, failed)


class AL3Checker(PatternChecker):
    """AL-3: Naive String Search → KMP — O(n*m) replaced with O(n+m)."""
    pattern_id = "AL-3"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # KMP hallmarks: failure function / lps array + two-pointer advance
        has_lps = bool(re.search(r'\blps\b|\bfailure\b|\bfail\b|\bpi\b', model_output, re.IGNORECASE))
        has_kmp_loop = bool(re.search(r'while\s*\([^)]*[jk]\s*>\s*0', model_output))
        slow_nested = bool(re.search(r'for[^}]*\{[^}]*for\s*\(', slow_code, re.DOTALL))
        if has_lps:
            passed.append("KMP failure/lps array detected")
        else:
            failed.append("no KMP failure function (lps/pi array) found")
        if slow_nested and not re.search(r'for[^}]*\{[^}]*for\s*\(', model_output, re.DOTALL):
            passed.append("nested O(n*m) loop replaced with single-pass KMP")
        elif slow_nested:
            failed.append("nested loop still present — naive O(n*m) may remain")
        return _result(passed, failed)


class AL4Checker(PatternChecker):
    """AL-4: Redundant Recursion → Memoization/Iterative."""
    pattern_id = "AL-4"

    def _ast_check(self, slow_code, model_output):
        slow_r = _RecursionChecker()
        out_r  = _RecursionChecker()
        slow_ast = _parse(slow_code)
        out_ast  = _parse(model_output)
        if slow_ast is None or out_ast is None:
            return None
        slow_r.visit(slow_ast)
        out_r.visit(out_ast)
        passed, failed = [], []
        if slow_r.recursive_calls > 0 and out_r.recursive_calls == 0:
            passed.append("recursion eliminated")
        elif out_r.recursive_calls > 0:
            failed.append(f"recursive calls remain ({out_r.recursive_calls})")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        has_memo = bool(re.search(r'\b(?:memo|cache|dp|visited)\s*[\[\(]', model_output))
        out_rec  = bool(re.search(r'\b(\w+)\s*\([^)]*\)[^{]*\{[^}]*\1\s*\(', model_output, re.DOTALL))
        if not out_rec:
            passed.append("no recursive call in output")
        else:
            failed.append("recursive call still present")
        if has_memo:
            passed.append("memoization/cache array detected")
        return _result(passed, failed)
