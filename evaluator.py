from dataclasses import dataclass
from typing import Optional

from compiler import compile_and_run, normalize_function_name, sanitize_llm_code, extract_code_from_response
from patterns import PatternEntry
from prompts import build_prompt


@dataclass
class EvalResult:
    pattern_id: str
    model: str
    strategy: str
    llm_code: str
    compiles: bool
    correct: bool
    slow_ms: float
    llm_ms: float
    ref_fast_ms: float
    speedup_vs_slow: float
    speedup_vs_ref: float
    diagnosed_pattern: Optional[str] = None
    hw_target: str = "generic"


def evaluate_pattern(pattern: PatternEntry, model: str, strategy: str,
                     call_llm_fn, hw_target: str = "generic",
                     max_retries: int = 3) -> EvalResult:
    """Evaluate a single pattern with a specific model and strategy.

    Retries up to max_retries times if the code fails to compile or produces
    wrong output, feeding the error back to the model each attempt.
    """
    prompt = build_prompt(pattern, strategy, hw_target)

    llm_code = ""
    result: dict = {"compiles": False, "correct": False, "time_ms": 0}

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            error_msg = result.get("error", "")
            if not result.get("compiles", False):
                feedback = (
                    f"\n\nYour previous attempt failed to compile with this error:\n"
                    f"{error_msg}\n\n"
                    f"Previous code:\n```c\n{llm_code}\n```\n\n"
                    f"Fix the code and return ONLY the corrected C function."
                )
            else:
                feedback = (
                    f"\n\nYour previous attempt compiled but produced wrong output.\n"
                    f"Previous code:\n```c\n{llm_code}\n```\n\n"
                    f"Fix the logic and return ONLY the corrected C function."
                )
            retry_prompt = prompt + feedback
        else:
            retry_prompt = prompt

        llm_response = call_llm_fn(retry_prompt, model)
        llm_code = extract_code_from_response(llm_response)

        if pattern.test_harness:
            llm_code = sanitize_llm_code(llm_code, pattern.test_harness)
            result = compile_and_run(llm_code, pattern.test_harness)
        else:
            result = {"compiles": False, "correct": False, "time_ms": 0}

        if result.get("compiles") and result.get("correct"):
            break

    slow_ms = 0.0
    ref_fast_ms = 0.0
    speedup_vs_slow = 0.0
    speedup_vs_ref = 0.0
    llm_ms = result.get("time_ms", 0)

    if pattern.test_harness and result.get("correct"):
        slow_ref = normalize_function_name(pattern.slow_code.strip())
        slow_ref = sanitize_llm_code(slow_ref, pattern.test_harness)
        slow_result = compile_and_run(slow_ref, pattern.test_harness)
        slow_ms = slow_result.get("time_ms", 0)

        fast_ref = normalize_function_name(pattern.fast_code.strip())
        fast_ref = sanitize_llm_code(fast_ref, pattern.test_harness)
        fast_result = compile_and_run(fast_ref, pattern.test_harness)
        ref_fast_ms = fast_result.get("time_ms", 0)

        if slow_ms > 0:
            speedup_vs_slow = slow_ms / llm_ms if llm_ms > 0 else 0
        if ref_fast_ms > 0:
            speedup_vs_ref = ref_fast_ms / llm_ms if llm_ms > 0 else 0

    return EvalResult(
        pattern_id=pattern.pattern_id,
        model=model,
        strategy=strategy,
        llm_code=llm_code,
        compiles=result.get("compiles", False),
        correct=result.get("correct", False),
        slow_ms=slow_ms,
        llm_ms=llm_ms,
        ref_fast_ms=ref_fast_ms,
        speedup_vs_slow=speedup_vs_slow,
        speedup_vs_ref=speedup_vs_ref,
        hw_target=hw_target,
    )
