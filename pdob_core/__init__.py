"""Pattern-Driven Optimization Benchmark — core library.

Convenience re-exports for the most common entry points.  Subpackages
(``pdob_core.patterns``, ``pdob_core.generators``) and individual
modules (``pdob_core.compiler``, ``pdob_core.evaluator``,
``pdob_core.prompts``, ``pdob_core.models``,
``pdob_core.dataset_evaluator``) remain importable directly.
"""

from .compiler import (
    compile_and_run,
    normalize_function_name,
    sanitize_llm_code,
    extract_code_from_response,
)
from .patterns import PATTERNS, PatternEntry
from .evaluator import EvalResult, evaluate_pattern, evaluate_variant
from .prompts import build_prompt

__all__ = [
    "PATTERNS",
    "PatternEntry",
    "EvalResult",
    "build_prompt",
    "compile_and_run",
    "evaluate_pattern",
    "evaluate_variant",
    "extract_code_from_response",
    "normalize_function_name",
    "sanitize_llm_code",
]
