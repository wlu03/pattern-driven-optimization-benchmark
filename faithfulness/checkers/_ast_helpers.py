"""
_ast_helpers.py
---------------
Shared AST + regex helpers for pattern checkers:

  * `_preprocess` — strip directives pycparser cannot handle
  * `_parse` — pycparser front-end (returns None on failure)
  * AST visitor classes (`_CallCollector`, `_LoopStats`, `_IfStats`, ...)
  * Convenience helpers (`_calls_at_depth`, `_loop_stats`, `_malloc_stats`,
    `_if_stats`) used by per-pattern checkers.

`HAS_PYCPARSER`, `_TYPE_STUBS`, and `_TRANSCENDENTAL` are exported so that
the package `__init__` can re-export them for compatibility.
"""

import re
from typing import Optional

try:
    import pycparser
    from pycparser import c_ast
    HAS_PYCPARSER = True
except ImportError:
    HAS_PYCPARSER = False


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
