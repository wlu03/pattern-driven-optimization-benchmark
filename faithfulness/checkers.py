"""
checkers.py
-----------
AST-based structural faithfulness checkers for all 32 optimization patterns.

For each pattern, checks whether the model output applied the expected
structural transformation — not just whether the output is faster.

Uses pycparser for AST analysis with regex fallback when parsing fails.

Install:
    pip install pycparser
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

try:
    import pycparser
    from pycparser import c_ast
    HAS_PYCPARSER = True
except ImportError:
    HAS_PYCPARSER = False


# ─────────────────────────────────────────────────────────────────────────────
# Result types
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
# C preprocessing — strip things pycparser cannot handle
# ─────────────────────────────────────────────────────────────────────────────

_TYPE_STUBS = """
typedef unsigned long size_t;
typedef unsigned int  uint32_t;
typedef long          int64_t;
typedef int           int32_t;
double sin(double x);
double cos(double x);
double tan(double x);
double log(double x);
double log2(double x);
double exp(double x);
double sqrt(double x);
double pow(double x, double y);
double fabs(double x);
double atan(double x);
double atan2(double y, double x);
double ceil(double x);
double floor(double x);
void  *malloc(size_t n);
void  *calloc(size_t n, size_t s);
void   free(void *p);
void  *memset(void *s, int c, size_t n);
void  *memcpy(void *dst, const void *src, size_t n);
void  *memmove(void *dst, const void *src, size_t n);
int    printf(const char *fmt, ...);
"""

_TRANSCENDENTAL = {
    "sin", "cos", "tan", "log", "log2", "exp", "sqrt", "pow",
    "fabs", "atan", "atan2", "ceil", "floor",
}


def _preprocess(code: str) -> str:
    code = re.sub(r'#\s*include\s*[<"][^>"]*[>"]', '', code)
    code = re.sub(r'#\s*define\s+\S+[^\n]*', '', code)
    code = re.sub(r'#\s*pragma\s+[^\n]*', '', code)
    code = re.sub(r'__attribute__\s*\(\(.*?\)\)', '', code, flags=re.DOTALL)
    code = re.sub(r'\b__restrict__?\b', '', code)
    code = re.sub(r'\b__inline__?\b', '', code)
    return _TYPE_STUBS + "\n" + code


def _parse(code: str):
    if not HAS_PYCPARSER:
        return None
    try:
        return pycparser.CParser().parse(_preprocess(code), filename="<input>")
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# AST visitors
# ─────────────────────────────────────────────────────────────────────────────

if HAS_PYCPARSER:

    class _CallCollector(c_ast.NodeVisitor):
        """Collect every FuncCall as (name, loop_depth)."""
        def __init__(self):
            self.calls: list[tuple[str, int]] = []
            self._depth = 0

        def _enter_loop(self, node):
            self._depth += 1; self.generic_visit(node); self._depth -= 1

        visit_For = visit_While = visit_DoWhile = _enter_loop

        def visit_FuncCall(self, node):
            name = node.name.name if isinstance(node.name, c_ast.ID) else None
            if name:
                self.calls.append((name, self._depth))
            self.generic_visit(node)

    class _LoopStats(c_ast.NodeVisitor):
        """Count loops and track max nesting depth."""
        def __init__(self):
            self.count = 0
            self.max_depth = 0
            self._depth = 0

        def _enter(self, node):
            self._depth += 1
            self.count += 1
            self.max_depth = max(self.max_depth, self._depth)
            self.generic_visit(node)
            self._depth -= 1

        visit_For = visit_While = visit_DoWhile = _enter

    class _IfStats(c_ast.NodeVisitor):
        """Count if-statements inside and outside loops."""
        def __init__(self):
            self.in_loop = 0
            self.outside = 0
            self._depth = 0

        def _enter_loop(self, node):
            self._depth += 1; self.generic_visit(node); self._depth -= 1

        visit_For = visit_While = visit_DoWhile = _enter_loop

        def visit_If(self, node):
            if self._depth > 0:
                self.in_loop += 1
            else:
                self.outside += 1
            self.generic_visit(node)

    class _MallocStats(c_ast.NodeVisitor):
        """Count malloc/calloc calls inside and outside loops."""
        def __init__(self):
            self.in_loop = 0
            self.outside = 0
            self._depth = 0

        def _enter_loop(self, node):
            self._depth += 1; self.generic_visit(node); self._depth -= 1

        visit_For = visit_While = visit_DoWhile = _enter_loop

        def visit_FuncCall(self, node):
            if isinstance(node.name, c_ast.ID) and node.name.name in ("malloc", "calloc"):
                if self._depth > 0:
                    self.in_loop += 1
                else:
                    self.outside += 1
            self.generic_visit(node)

    class _RecursionChecker(c_ast.NodeVisitor):
        """Detect recursive calls within a function definition."""
        def __init__(self):
            self.recursive_calls = 0
            self._current = None

        def visit_FuncDef(self, node):
            prev, self._current = self._current, node.decl.name
            self.generic_visit(node)
            self._current = prev

        def visit_FuncCall(self, node):
            if isinstance(node.name, c_ast.ID) and node.name.name == self._current:
                self.recursive_calls += 1
            self.generic_visit(node)

    class _OuterLoopVar(c_ast.NodeVisitor):
        """Get the iteration variable of the outermost for-loop."""
        def __init__(self):
            self.outer_vars: list[str] = []
            self._depth = 0

        def visit_For(self, node):
            if self._depth == 0 and node.init:
                if hasattr(node.init, "decls") and node.init.decls:
                    self.outer_vars.append(node.init.decls[0].name)
                elif isinstance(node.init, c_ast.Assignment):
                    if isinstance(node.init.lvalue, c_ast.ID):
                        self.outer_vars.append(node.init.lvalue.name)
            self._depth += 1
            self.generic_visit(node)
            self._depth -= 1

    class _ArrayDeclCount(c_ast.NodeVisitor):
        """Count local array declarations."""
        def __init__(self):
            self.count = 0

        def visit_ArrayDecl(self, node):
            self.count += 1
            self.generic_visit(node)

    class _StructParamChecker(c_ast.NodeVisitor):
        """Check if any function parameter is a struct type."""
        def __init__(self):
            self.has_struct_param = False

        def visit_FuncDef(self, node):
            if node.decl.type.args:
                for p in (node.decl.type.args.params or []):
                    typ = p.type
                    # Unwrap pointer
                    if isinstance(typ, c_ast.PtrDecl):
                        typ = typ.type
                    if isinstance(typ, c_ast.Struct):
                        self.has_struct_param = True
                    elif isinstance(typ, (c_ast.IdentifierType,)):
                        pass
            self.generic_visit(node)


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


# ─────────────────────────────────────────────────────────────────────────────
# Shared AST helpers
# ─────────────────────────────────────────────────────────────────────────────

def _calls_at_depth(code: str) -> Optional[list[tuple[str, int]]]:
    ast = _parse(code)
    if ast is None:
        return None
    v = _CallCollector()
    v.visit(ast)
    return v.calls


def _loop_stats(code: str) -> Optional[tuple[int, int]]:
    """Returns (loop_count, max_depth) or None."""
    ast = _parse(code)
    if ast is None:
        return None
    v = _LoopStats()
    v.visit(ast)
    return v.count, v.max_depth


def _malloc_stats(code: str) -> Optional[tuple[int, int]]:
    """Returns (in_loop, outside) or None."""
    ast = _parse(code)
    if ast is None:
        return None
    v = _MallocStats()
    v.visit(ast)
    return v.in_loop, v.outside


def _if_stats(code: str) -> Optional[tuple[int, int]]:
    """Returns (in_loop, outside) or None."""
    ast = _parse(code)
    if ast is None:
        return None
    v = _IfStats()
    v.visit(ast)
    return v.in_loop, v.outside


# ─────────────────────────────────────────────────────────────────────────────
# SR — Semantic Redundancy
# ─────────────────────────────────────────────────────────────────────────────

class SR1Checker(PatternChecker):
    """SR-1: Loop-Invariant Function Call — expensive fn hoisted outside loop."""
    pattern_id = "SR-1"

    def _ast_check(self, slow_code, model_output):
        calls = _calls_at_depth(model_output)
        if calls is None:
            return None
        passed, failed = [], []
        expensive_in_loop = [n for n, d in calls if n in _TRANSCENDENTAL and d > 0]
        if expensive_in_loop:
            failed.append(f"transcendental call(s) {expensive_in_loop} still inside loop")
        else:
            passed.append("no transcendental calls inside loop body")
        expensive_outside = [n for n, d in calls if n in _TRANSCENDENTAL and d == 0]
        if expensive_outside:
            passed.append(f"transcendental call(s) {expensive_outside} hoisted outside loop")
        else:
            failed.append("no hoisted transcendental call found outside loop")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        fns = "|".join(_TRANSCENDENTAL)
        in_loop = re.search(
            r'for\s*\([^)]*\)\s*\{[^}]*(?:' + fns + r')\s*\(',
            model_output, re.DOTALL
        )
        if in_loop:
            failed.append("transcendental call appears to be inside loop")
        else:
            passed.append("no transcendental call detected inside loop")
        if re.search(r'(?:' + fns + r')\s*\(', model_output):
            passed.append("transcendental call present (likely hoisted)")
        return _result(passed, failed)


class SR2Checker(PatternChecker):
    """SR-2: Expression Decomposition — subexpression cached before loop."""
    pattern_id = "SR-2"

    def _ast_check(self, slow_code, model_output):
        slow_calls = _calls_at_depth(slow_code) or []
        out_calls  = _calls_at_depth(model_output) or []
        slow_count_in = sum(1 for _, d in slow_calls if d > 0)
        out_count_in  = sum(1 for _, d in out_calls  if d > 0)
        passed, failed = [], []
        if out_count_in < slow_count_in:
            passed.append(f"calls inside loop reduced: {slow_count_in} → {out_count_in}")
        else:
            failed.append(f"calls inside loop not reduced ({out_count_in} vs slow {slow_count_in})")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Look for a scalar temp assigned before first for-loop
        if re.search(r'(?:int|float|double)\s+\w+\s*=[^;]+;[^{]*for\s*\(', model_output, re.DOTALL):
            passed.append("scalar pre-computed before loop detected")
        else:
            failed.append("no pre-loop scalar computation detected")
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
        if slow_stats[1] >= 2 and out_stats[1] < 2:
            passed.append(f"nested loops eliminated: max depth {slow_stats[1]} → {out_stats[1]}")
        elif out_stats[1] >= 2:
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


# ─────────────────────────────────────────────────────────────────────────────
# IS — Input-Sensitive
# ─────────────────────────────────────────────────────────────────────────────

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
        # Extract noinline function names from slow code
        noinline = re.findall(r'__attribute__.*?noinline.*?\n\w[\w\s\*]*?(\w+)\s*\(', slow_code, re.DOTALL)
        if not noinline:
            noinline = re.findall(r'\bnoinline\b.*?(\w+)\s*\(', slow_code)
        has_branch_guard = bool(re.search(r'if\s*\([^)]*\)\s*\{[^}]*\}', model_output))
        if has_branch_guard:
            passed.append("conditional branch guards expensive call")
        else:
            failed.append("no conditional guard around expensive call")
        # Check that fabs or threshold comparison appears (the outlier check pattern)
        if re.search(r'\bfabs\b|\babs\b|>\s*thresh|<\s*thresh', model_output):
            passed.append("threshold comparison detected (outlier branching)")
        else:
            failed.append("no threshold comparison detected")
        return _result(passed, failed)


class IS3Checker(PatternChecker):
    """IS-3: Already-Sorted Check — skip sort if input is already sorted."""
    pattern_id = "IS-3"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        has_sort_check = bool(re.search(
            r'for\s*\([^)]*\)[^{]*\{[^}]*(?:\[\s*i\s*\]\s*>\s*\w*\[\s*i\s*[+-]\s*1\s*\]'
            r'|\[\s*i\s*[+-]\s*1\s*\]\s*<\s*\w*\[\s*i\s*\])[^}]*\}',
            model_output, re.DOTALL
        ))
        has_early_return = bool(re.search(r'\breturn\b', model_output))
        if has_sort_check or re.search(r'sorted|is_sorted|already', model_output, re.IGNORECASE):
            passed.append("sorted-check pattern detected")
        else:
            failed.append("no sorted-check before sort call")
        if has_early_return:
            passed.append("early return present")
        else:
            failed.append("no early return for already-sorted case")
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


# ─────────────────────────────────────────────────────────────────────────────
# CF — Control Flow
# ─────────────────────────────────────────────────────────────────────────────

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
        # Fast version should have if BEFORE loop, then separate loops per branch
        if re.search(r'if\s*\([^)]*mode[^)]*\)[^{]*\{[^}]*for\s*\(', model_output, re.DOTALL):
            passed.append("dispatch conditional precedes loop (hoisted)")
        elif re.search(r'if\s*\(.*\)\s*\{', model_output) and re.search(r'for\s*\(', model_output):
            passed.append("if-statement and loop both present (likely restructured)")
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
    """CF-3: Vectorization-Hostile Conditional — guard removed or proven always-true."""
    pattern_id = "CF-3"

    def _ast_check(self, slow_code, model_output):
        slow_if = _if_stats(slow_code)
        out_if  = _if_stats(model_output)
        if slow_if is None or out_if is None:
            return None
        passed, failed = [], []
        if out_if[0] < slow_if[0]:
            passed.append(f"conditionals in loop reduced: {slow_if[0]} → {out_if[0]}")
        else:
            failed.append("conditional in loop not removed")
        return _result(passed, failed)

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_ifs_in_loop = len(re.findall(
            r'for\s*\([^)]*\)\s*\{[^}]*\bif\b[^}]*\}', slow_code, re.DOTALL))
        out_ifs_in_loop  = len(re.findall(
            r'for\s*\([^)]*\)\s*\{[^}]*\bif\b[^}]*\}', model_output, re.DOTALL))
        if out_ifs_in_loop < slow_ifs_in_loop:
            passed.append(f"if-statements in loop body reduced: {slow_ifs_in_loop} → {out_ifs_in_loop}")
        else:
            failed.append("if-statements in loop body not reduced")
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


# ─────────────────────────────────────────────────────────────────────────────
# HR — Human-Style Antipatterns
# ─────────────────────────────────────────────────────────────────────────────

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
        # Null/bounds check before loop
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
        return _result(passed, failed)


class HR5Checker(PatternChecker):
    """HR-5: Redundant Re-initialization — repeated memset/zero-fill removed."""
    pattern_id = "HR-5"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        slow_zeros = len(re.findall(r'\bmemset\s*\(|\bfor[^}]*=\s*0\s*;', slow_code))
        out_zeros  = len(re.findall(r'\bmemset\s*\(|\bfor[^}]*=\s*0\s*;', model_output))
        if slow_zeros > 0 and out_zeros < slow_zeros:
            passed.append(f"redundant zero-initialization reduced: {slow_zeros} → {out_zeros}")
        elif slow_zeros > 0:
            failed.append("zero-initialization not reduced")
        else:
            passed.append("no obvious redundant zero-init in slow code")
        return _result(passed, failed)


# ─────────────────────────────────────────────────────────────────────────────
# DS — Data Structure Choice
# ─────────────────────────────────────────────────────────────────────────────

class DS1Checker(PatternChecker):
    """DS-1: Linear Search → Hash Table — O(n) lookup replaced with O(1)."""
    pattern_id = "DS-1"

    def _regex_check(self, slow_code, model_output):
        passed, failed = [], []
        # Hash table: uses modulo for bucket indexing
        has_hash = bool(re.search(r'\s%\s*\w+|\bHASH\b|\bhash\b|\bbucket\b|\btable\b', model_output))
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


# ─────────────────────────────────────────────────────────────────────────────
# AL — Algorithmic Inefficiency
# ─────────────────────────────────────────────────────────────────────────────

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
        if out_a.count > slow_a.count:
            passed.append("DP array introduced (memo table)")
        elif out_a.count == 0 and slow_r.recursive_calls > 0:
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


# ─────────────────────────────────────────────────────────────────────────────
# MI — Memory / IO
# ─────────────────────────────────────────────────────────────────────────────

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
    """MI-2: Redundant Multi-Pass — 3-pass with heap arrays → single-pass."""
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
        if slow_mallocs > 0 and out_mallocs < slow_mallocs:
            passed.append(f"malloc reduced: {slow_mallocs} → {out_mallocs}")
        elif slow_mallocs > 0:
            failed.append("intermediate mallocs not removed")
        if out_loops < slow_loops:
            passed.append(f"loop count reduced: {slow_loops} → {out_loops}")
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
            o_outer = out_v.outer_vars[0]
            if s_outer != o_outer:
                passed.append(f"outer loop variable changed: '{s_outer}' → '{o_outer}' (loop order swapped)")
            else:
                failed.append(f"outer loop variable unchanged ('{o_outer}') — loop order may not be swapped")
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


# ─────────────────────────────────────────────────────────────────────────────
# COMP — Composed Patterns
# ─────────────────────────────────────────────────────────────────────────────

class COMPChecker(PatternChecker):
    """COMP: Multiple overlapping patterns — at least 2 constituent fixes applied."""
    pattern_id = "COMP"

    def check(self, slow_code: str, model_output: str) -> FaithfulnessResult:
        # Run a battery of lightweight checks; require at least 2 to pass
        sub_checks = [
            ("no recursion",      lambda: not bool(re.search(r'\b(\w+)\s*\([^)]*\)[^{]*\{[^}]*\1\s*\(', model_output, re.DOTALL))),
            ("reduced loops",     lambda: len(re.findall(r'\bfor\s*\(', model_output)) < len(re.findall(r'\bfor\s*\(', slow_code))),
            ("reduced malloc",    lambda: len(re.findall(r'\bmalloc\s*\(', model_output)) < len(re.findall(r'\bmalloc\s*\(', slow_code))),
            ("if hoisted",        lambda: not bool(re.search(r'for[^{]*\{[^}]*\bif\b[^}]*mode[^}]*\}', model_output, re.DOTALL))),
            ("no struct param",   lambda: not bool(re.search(r'\bstruct\b\s+\w+\s*\*', model_output)) and bool(re.search(r'\bstruct\b\s+\w+\s*\*', slow_code))),
            ("reduced mallocs",   lambda: len(re.findall(r'\bmalloc\b', model_output)) <= len(re.findall(r'\bmalloc\b', slow_code))),
            ("no null in loop",   lambda: not bool(re.search(r'for[^{]*\{[^}]*NULL[^}]*\}', model_output, re.DOTALL))),
        ]
        passed, failed = [], []
        for name, fn in sub_checks:
            try:
                if fn():
                    passed.append(name)
                else:
                    failed.append(name)
            except Exception:
                pass
        score = len(passed) / max(len(passed) + len(failed), 1)
        if len(passed) >= 2:
            verdict = Verdict.FAITHFUL if score >= 0.6 else Verdict.PARTIAL
            expl = f"{len(passed)} of {len(passed)+len(failed)} composite checks passed"
        else:
            verdict = Verdict.UNFAITHFUL
            expl = "fewer than 2 constituent pattern fixes detected"
        return FaithfulnessResult(verdict, score, expl, passed, failed)

    def _regex_check(self, slow_code, model_output):
        return _unknown("use check() directly")


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
}


def check_faithfulness(
    pattern_id: str,
    slow_code: str,
    model_output: str,
) -> FaithfulnessResult:
    """
    Main entry point. Returns a FaithfulnessResult for the given pattern.

    Args:
        pattern_id:   e.g. "SR-1", "AL-3", "COMP"
        slow_code:    contents of slow.c
        model_output: the model's optimized C code
    """
    checker = CHECKERS.get(pattern_id)
    if checker is None:
        return _unknown(f"no checker implemented for pattern '{pattern_id}'")
    try:
        return checker.check(slow_code, model_output)
    except Exception as e:
        return _unknown(f"checker raised exception: {e}")
