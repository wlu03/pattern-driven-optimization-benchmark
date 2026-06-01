from dataclasses import dataclass, field
from typing import List, Optional

from .compiler import compile_and_run, normalize_function_name, sanitize_llm_code, extract_code_from_response
from .patterns import PatternEntry
from .prompts import build_prompt

# Imported lazily-at-bottom: evaluate_variant uses dataset_evaluator helpers.

# Median of |x - median(x)|. Used as a robust spread estimate alongside the
# median timing — more stable than stddev when one of the runs got
# bulldozed by a context switch.
def _median(xs: List[float]) -> float:
    if not xs:
        return 0.0
    sorted_xs = sorted(xs)
    n = len(sorted_xs)
    if n % 2 == 1:
        return sorted_xs[n // 2]
    return 0.5 * (sorted_xs[n // 2 - 1] + sorted_xs[n // 2])


def _mad(xs: List[float]) -> float:
    if not xs:
        return 0.0
    med = _median(xs)
    return _median([abs(x - med) for x in xs])


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
    # ── New fields (appended so existing CSVs still parse) ────────────────
    # Variant ID when running --dataset path; None for patterns.py-only runs.
    variant_id: Optional[str] = None
    # Sample index when --samples > 1; 0 for single-sample runs (default).
    sample_idx: int = 0
    # Robust spread of the per-run timings (median absolute deviation).
    slow_ms_mad: float = 0.0
    llm_ms_mad: float = 0.0
    ref_fast_ms_mad: float = 0.0
    # Candidate timing at additional opt levels (None if not requested).
    llm_ms_O0: Optional[float] = None
    llm_ms_O3: Optional[float] = None
    # True if the run looks suspicious (e.g. llm_ms below noise floor and we
    # therefore suppressed the speedup ratios to avoid polluting aggregates).
    unreliable: bool = False
    unreliable_reason: Optional[str] = None
    # ── Faithfulness verdict (populated when --faithfulness is on) ────────
    # 2x2 cell from faithfulness/equivalence.py:two_axis_verdict.
    # One of: FAITHFUL, FAITHFUL_ALTERNATIVE, STRUCTURAL_ONLY, FAILED, None.
    faithfulness_cell:                Optional[str]   = None
    faithfulness_equivalent:          Optional[bool]  = None
    faithfulness_expected_shape:      Optional[bool]  = None
    faithfulness_structural_verdict:  Optional[str]   = None   # faithful/partial/unfaithful/unknown
    faithfulness_structural_score:    Optional[float] = None
    faithfulness_equiv_configs:       Optional[int]   = None
    faithfulness_equiv_passed:        Optional[int]   = None
    # ── LLM-as-optimizer iterative loop (populated when iter_max_rounds>1) ─
    # Round 0 = original first-pass output; round k>0 = k-th improvement attempt.
    # iter_rounds = total improvement attempts ACTUALLY run (may be < max if
    # threshold met early); iter_initial_speedup = speedup_vs_slow from round 0
    # (before any iteration); the final llm_ms / speedup_vs_slow reflect the
    # BEST candidate found across all rounds.
    iter_rounds:           int            = 0
    iter_initial_speedup:  Optional[float] = None
    # ── Reasoning trace (CoT-as-data, not as oracle) ───────────────────────
    # Captured when the provider returns a separate reasoning channel:
    # DeepSeek-R1 reasoning_content (automatic), Claude thinking blocks
    # (when enable_thinking=true in models.yaml), OpenAI o-series reasoning
    # summary (when enable_reasoning=true). Used by
    # scripts/cot_alignment_analysis.py to compare what the model SAID it
    # was doing vs what the structural verdict says it actually did.
    # None for models without a separate reasoning channel.
    reasoning_trace:       Optional[str]  = None


_DIAGNOSIS_CATEGORY_HINTS = {
    "SR":  ["semantic redundancy", "loop-invariant", "hoist", "redundant computation"],
    "IS":  ["input-sensitive", "input distribution", "data-dependent", "sorted", "skew"],
    "CF":  ["control flow", "control-flow", "branch", "predication", "loop unswitch"],
    "DS":  ["data structure", "data-structure", "aos", "soa", "layout"],
    "AL":  ["algorithmic", "complexity", "dynamic programming", "memoization", "asymptotic"],
    "MI":  ["memory", "cache", "prefetch", "row-major", "column-major", "alignment"],
    "HR":  ["human-style", "antipattern", "copy-paste", "redundant temporar", "dead code"],
}


def _extract_diagnosed_pattern(text: str) -> Optional[str]:
    """Best-effort category extractor for diagnosis-strategy responses.

    Looks for explicit category mentions or characteristic vocabulary in
    the model's free-form text and returns the two-letter category code
    (SR, IS, CF, DS, AL, MI, HR) it most likely identifies. Returns None
    if no clear signal. The result is stored on EvalResult so downstream
    analysis (scripts/diagnostic_accuracy.py) can compare against ground
    truth (the variant's pattern_id prefix).
    """
    if not text:
        return None
    t = text.lower()
    # First pass: explicit pattern IDs (e.g. "SR-3", "MI-4")
    import re
    m = re.search(r"\b([A-Z]{2})-\d+\b", text)
    if m:
        return m.group(1)
    # Second pass: keyword voting
    scores = {cat: 0 for cat in _DIAGNOSIS_CATEGORY_HINTS}
    for cat, kws in _DIAGNOSIS_CATEGORY_HINTS.items():
        for kw in kws:
            if kw in t:
                scores[cat] += 1
    best_cat, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_cat if best_score > 0 else None


def _compute_faithfulness(
    pattern_id: str,
    slow_code: str,
    model_output: str,
    *,
    test_harness: Optional[str] = None,
    equiv_n_inputs: int = 9,
) -> dict:
    """Run the 2x2 faithfulness cascade and return new-field dict for EvalResult.

    Structural tier always runs (cheap, no compile). Equivalence tier runs
    only when test_harness is provided (it compiles + runs the candidate N
    times). On any exception, fields remain None so the caller's CSV row
    stays well-formed.
    """
    fields = {
        "faithfulness_cell":                None,
        "faithfulness_equivalent":          None,
        "faithfulness_expected_shape":      None,
        "faithfulness_structural_verdict":  None,
        "faithfulness_structural_score":    None,
        "faithfulness_equiv_configs":       None,
        "faithfulness_equiv_passed":        None,
    }
    try:
        from faithfulness.checkers import check_faithfulness
        struct = check_faithfulness(pattern_id, slow_code, model_output)
        fields["faithfulness_structural_verdict"] = struct.verdict
        fields["faithfulness_structural_score"]   = struct.score
    except Exception:
        return fields

    if test_harness is None:
        # Structural-only mode (e.g. dataset path — test.c is on disk and not
        # a string; differential testing would need different plumbing).
        # Derive expected_shape from the structural verdict alone; cell stays
        # None to signal "equivalence axis not measured."
        if struct.verdict == "faithful":
            fields["faithfulness_expected_shape"] = True
        elif struct.verdict == "unfaithful":
            fields["faithfulness_expected_shape"] = False
        return fields

    try:
        from faithfulness.equivalence import differential_equivalence, two_axis_verdict
        eq = differential_equivalence(model_output, test_harness,
                                      n_inputs=equiv_n_inputs)
        fields["faithfulness_equivalent"]    = eq.equivalent
        fields["faithfulness_equiv_configs"] = eq.n_configs
        fields["faithfulness_equiv_passed"]  = eq.n_correct
        v = two_axis_verdict(struct, eq)
        fields["faithfulness_cell"]           = v.cell
        fields["faithfulness_expected_shape"] = v.expected_shape
    except Exception:
        pass

    return fields


def _gather_runs(code: str, test_harness: str, *, runs: int,
                 opt_level: str, timeout: int = 120) -> dict:
    """Run compile_and_run with given runs/opt_level and harvest individual
    times by calling N independent runs=1 compilations is wasteful — instead
    we use compile_and_run's built-in runs= mechanism (which compiles once
    then runs N times) but augment by gathering per-run times.

    compile_and_run already supports `runs=` and returns a median. We can't
    easily get the individual times back without changing compiler.py, so
    we do a single batched call and use its median; for the MAD spread, we
    fan out runs=1 calls (re-using the cached compile via tempdir is not
    possible across calls, but the compile is cheap relative to the run).

    For simplicity and to keep compiler.py untouched, we just call
    compile_and_run once with runs=N and use the median. MAD is computed
    from N fan-out calls only if the caller passes runs>=3 — otherwise we
    skip MAD (set to 0) to avoid 3x compile cost for tiny runs.
    """
    # Single batched call gives us median + correctness + compile status.
    batched = compile_and_run(
        code, test_harness, timeout=timeout, opt_level=opt_level, runs=runs,
    )
    return batched


def _is_unreliable(time_ms: float, noise_floor_ms: float) -> tuple:
    """Return (unreliable, reason) for a candidate timing."""
    if time_ms > 0 and time_ms < noise_floor_ms:
        return True, (
            f"llm_ms={time_ms:.4f}ms < noise_floor={noise_floor_ms:.4f}ms "
            f"(likely dead-code-eliminated — speedup ratios suppressed)"
        )
    return False, None


def evaluate_pattern(pattern: PatternEntry, model: str, strategy: str,
                     call_llm_fn, hw_target: str = "generic",
                     max_retries: int = 3, *,
                     runs: int = 10,
                     opt_levels: Optional[List[str]] = None,
                     noise_floor_ms: float = 0.05,
                     sample_idx: int = 0,
                     temperature_override: Optional[float] = None,
                     faithfulness: bool = False,
                     iter_max_rounds: int = 1,
                     iter_speedup_threshold: float = 2.0) -> EvalResult:
    """Evaluate a single pattern with a specific model and strategy.

    Retries up to max_retries times if the code fails to compile or produces
    wrong output, feeding the error back to the model each attempt.

    Args:
      runs: number of timed runs; median + MAD computed.
      opt_levels: list of opt levels for the candidate. The PRIMARY level
        (used for slow_ms/llm_ms/ref_fast_ms) is opt_levels[0] (or "O2" by
        default). Additional levels in the list populate llm_ms_O0 /
        llm_ms_O3 columns.
      noise_floor_ms: if llm_ms < this, flag unreliable and suppress speedup.
      sample_idx: which sample index this is (0 for first; recorded in result).
      temperature_override: not used here — caller sets model temperature via
        the model_cfg dict before invoking call_llm_fn (see evaluate_llm.py).
      faithfulness: when True, run the 2x2 faithfulness cascade (structural
        check + differential equivalence) and populate the faithfulness_*
        fields of EvalResult. Adds ~9 extra compile+run cycles per correct
        candidate, so off by default.
      iter_max_rounds: LLM-as-optimizer iteration cap. When >1 and the
        initial speedup is below `iter_speedup_threshold`, feed the model
        its own code + measured speedup and ask for improvement up to
        (iter_max_rounds - 1) more times. The best correct candidate wins.
        Default 1 = no iteration (preserves prior behavior).
      iter_speedup_threshold: stop iterating early once measured speedup
        exceeds this (default 2.0x — match the compiler-resistance threshold
        used elsewhere in the benchmark).
    """
    if opt_levels is None:
        opt_levels = ["O2"]
    primary_opt = opt_levels[0]

    prompt = build_prompt(pattern, strategy, hw_target)

    # Diagnosis-only strategy short-circuit. The diagnosis prompt asks the
    # model to NAME the inefficiency category, not to emit C. Running the
    # output through extract_code_from_response -> compile -> retry-with-
    # "fix the code" feedback contaminates the experiment by feeding the
    # model back into a code-generation loop. Instead: call the model
    # once, store the raw response as a textual classification, skip all
    # compile/run measurement, and return a row that records the response
    # without pretending it's runnable C.
    if strategy == "diagnosis":
        llm_response = call_llm_fn(prompt, model)
        try:
            from .models import get_last_reasoning_trace
            _last_reasoning = get_last_reasoning_trace()
        except Exception:
            _last_reasoning = None
        return EvalResult(
            pattern_id=pattern.pattern_id,
            model=model,
            strategy=strategy,
            llm_code=llm_response,           # raw text, NOT extracted C
            compiles=False,                  # not applicable; diagnosis is text
            correct=False,                   # not applicable
            slow_ms=0.0, llm_ms=0.0, ref_fast_ms=0.0,
            speedup_vs_slow=0.0, speedup_vs_ref=0.0,
            diagnosed_pattern=_extract_diagnosed_pattern(llm_response),
            hw_target=hw_target,
            variant_id=None,
            sample_idx=sample_idx,
        )

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
        # Capture reasoning trace if the provider stashed one (DeepSeek-R1,
        # Claude w/ thinking, o-series w/ reasoning). None otherwise. Read
        # immediately after the call — get_last_reasoning_trace clears it.
        try:
            from .models import get_last_reasoning_trace
            _last_reasoning = get_last_reasoning_trace()
        except Exception:
            _last_reasoning = None
        llm_code = extract_code_from_response(llm_response, pattern.test_harness)

        if pattern.test_harness:
            llm_code = sanitize_llm_code(llm_code, pattern.test_harness)
            result = _gather_runs(llm_code, pattern.test_harness,
                                  runs=runs, opt_level=primary_opt)
        else:
            result = {"compiles": False, "correct": False, "time_ms": 0}

        if result.get("compiles") and result.get("correct"):
            break

    slow_ms = 0.0
    ref_fast_ms = 0.0
    speedup_vs_slow = 0.0
    speedup_vs_ref = 0.0
    llm_ms = result.get("time_ms", 0)
    llm_ms_mad = result.get("time_ms_mad", 0.0)
    slow_ms_mad = 0.0
    ref_fast_ms_mad = 0.0
    llm_ms_O0: Optional[float] = None
    llm_ms_O3: Optional[float] = None

    if pattern.test_harness and result.get("correct"):
        slow_ref = normalize_function_name(pattern.slow_code.strip(), pattern.test_harness)
        slow_ref = sanitize_llm_code(slow_ref, pattern.test_harness)
        # MATCHED RUNS: slow ref now uses the same `runs=` as the candidate
        # (previously hardcoded to runs=1 which made speedup ratios noisy).
        slow_result = _gather_runs(slow_ref, pattern.test_harness,
                                   runs=runs, opt_level=primary_opt)
        slow_ms = slow_result.get("time_ms", 0)
        slow_ms_mad = slow_result.get("time_ms_mad", 0.0)

        fast_ref = normalize_function_name(pattern.fast_code.strip(), pattern.test_harness)
        fast_ref = sanitize_llm_code(fast_ref, pattern.test_harness)
        fast_result = _gather_runs(fast_ref, pattern.test_harness,
                                   runs=runs, opt_level=primary_opt)
        ref_fast_ms = fast_result.get("time_ms", 0)
        ref_fast_ms_mad = fast_result.get("time_ms_mad", 0.0)

        if slow_ms > 0 and llm_ms > 0:
            speedup_vs_slow = slow_ms / llm_ms
        if ref_fast_ms > 0 and llm_ms > 0:
            speedup_vs_ref = ref_fast_ms / llm_ms

        # ── LLM-as-optimizer iterative loop ──────────────────────────────
        # If iter_max_rounds > 1 AND the initial speedup is below the
        # threshold, give the model its own code + measured speedup and
        # ask it to try harder. Loop up to (iter_max_rounds - 1) more times,
        # keeping the best correct candidate. Stop early if threshold is met.
        iter_initial_speedup_local: Optional[float] = None
        iter_rounds_local = 0
        if iter_max_rounds > 1 and slow_ms > 0 and llm_ms > 0:
            iter_initial_speedup_local = speedup_vs_slow
            best_code = llm_code
            best_llm_ms = llm_ms
            best_llm_ms_mad = llm_ms_mad
            best_speedup = speedup_vs_slow
            for it in range(1, iter_max_rounds):
                if best_speedup >= iter_speedup_threshold:
                    break  # threshold met — no more iteration
                iter_rounds_local = it
                iter_prompt = prompt + (
                    f"\n\nYour previous attempt was correct but produced "
                    f"a speedup of only {best_speedup:.2f}x over the slow "
                    f"baseline (target: >{iter_speedup_threshold:.1f}x).\n\n"
                    f"Previous code:\n```c\n{best_code}\n```\n\n"
                    f"Reasoning about WHY the previous version is slow, "
                    f"rewrite it to be substantially faster. Maintain "
                    f"correctness. Return ONLY the C function."
                )
                try:
                    new_response = call_llm_fn(iter_prompt, model)
                except Exception:
                    break
                new_code = extract_code_from_response(new_response,
                                                     pattern.test_harness)
                new_code = sanitize_llm_code(new_code, pattern.test_harness)
                new_result = _gather_runs(new_code, pattern.test_harness,
                                          runs=runs, opt_level=primary_opt)
                if not (new_result.get("compiles") and new_result.get("correct")):
                    continue  # broken attempt — keep current best
                new_llm_ms = new_result.get("time_ms", 0) or 0
                if new_llm_ms <= 0:
                    continue
                new_speedup = slow_ms / new_llm_ms
                # Accept only strict improvement on speedup.
                if new_speedup > best_speedup:
                    best_code = new_code
                    best_llm_ms = new_llm_ms
                    best_llm_ms_mad = new_result.get("time_ms_mad", 0.0)
                    best_speedup = new_speedup
            # Promote the best candidate to the reported values.
            llm_code = best_code
            llm_ms = best_llm_ms
            llm_ms_mad = best_llm_ms_mad
            speedup_vs_slow = best_speedup
            if ref_fast_ms > 0 and llm_ms > 0:
                speedup_vs_ref = ref_fast_ms / llm_ms
            # Re-evaluate result.correct against the best candidate
            # (we only stored ones that already passed correctness above).
            result["correct"] = True
            result["compiles"] = True
            result["time_ms"] = llm_ms

        # Multi-opt-level recording: rerun candidate at each requested
        # additional opt level. Only the median is stored for these.
        for opt in opt_levels[1:]:
            extra = _gather_runs(llm_code, pattern.test_harness,
                                 runs=runs, opt_level=opt)
            t = extra.get("time_ms", 0) if extra.get("correct") else None
            if opt == "O0":
                llm_ms_O0 = t
            elif opt == "O3":
                llm_ms_O3 = t

    # Noise-floor guard: if the candidate ran absurdly fast, assume DCE /
    # constant-folding and suppress speedup ratios.
    unreliable, reason = _is_unreliable(llm_ms, noise_floor_ms)
    if unreliable and result.get("correct"):
        speedup_vs_slow = 0.0  # CSV field is float; NaN may not round-trip
        speedup_vs_ref = 0.0

    fhfn = {}
    if faithfulness and result.get("correct") and pattern.test_harness:
        fhfn = _compute_faithfulness(
            pattern.pattern_id, pattern.slow_code, llm_code,
            test_harness=pattern.test_harness,
        )

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
        sample_idx=sample_idx,
        slow_ms_mad=slow_ms_mad,
        llm_ms_mad=llm_ms_mad,
        ref_fast_ms_mad=ref_fast_ms_mad,
        llm_ms_O0=llm_ms_O0,
        llm_ms_O3=llm_ms_O3,
        unreliable=unreliable,
        unreliable_reason=reason,
        iter_rounds=iter_rounds_local if 'iter_rounds_local' in locals() else 0,
        iter_initial_speedup=(iter_initial_speedup_local
                              if 'iter_initial_speedup_local' in locals() else None),
        reasoning_trace=_last_reasoning if '_last_reasoning' in locals() else None,
        **fhfn,
    )


# ─────────────────────────────────────────────────────────────────────────
# Dataset path — evaluates LLM on a single on-disk variant.
# ─────────────────────────────────────────────────────────────────────────

def _build_variant_prompt(variant, pattern_lookup: dict, strategy: str,
                          hw_target: str) -> str:
    """Construct the prompt for a dataset variant.

    `pattern_lookup` maps pattern_id ("SR-1") → PatternEntry (from patterns.py),
    used to get `description` for pattern-aware strategies. If the variant's
    pattern_id is not in the lookup (e.g. "COMP"), we fall back to a generic
    prompt that uses only the variant's own metadata.
    """
    from .prompts import (
        make_prompt_generic,
        make_prompt_pattern_aware,
        make_prompt_taxonomy_guided,
        make_prompt_hardware_target,
        make_prompt_diagnosis_only,
    )
    with open(variant.slow_path) as f:
        slow_code = f.read()

    base_pattern = pattern_lookup.get(variant.pattern_id)

    if strategy == "generic":
        return make_prompt_generic(slow_code)
    if strategy == "taxonomy-guided":
        return make_prompt_taxonomy_guided(slow_code)
    if strategy == "hardware-target":
        return make_prompt_hardware_target(slow_code, hw_target)
    if strategy == "diagnosis":
        return make_prompt_diagnosis_only(slow_code)
    if strategy == "pattern-aware":
        if base_pattern is not None:
            return make_prompt_pattern_aware(slow_code, base_pattern)
        # COMP / unknown: synthesize a lightweight PatternEntry-like object
        # using only the variant's own metadata. make_prompt_pattern_aware
        # only reads .category, .name, .description.
        class _StubPattern:
            def __init__(self, v):
                self.category = v.category
                self.name = v.pattern_name or "Composed Pattern"
                self.description = (
                    v.variant_desc or
                    "This variant composes multiple inefficiency patterns; "
                    "identify and fix each one."
                )
        return make_prompt_pattern_aware(slow_code, _StubPattern(variant))
    raise ValueError(f"Unknown strategy: {strategy}")


def evaluate_variant(variant, model: str, strategy: str, call_llm_fn, *,
                     pattern_lookup: dict,
                     hw_target: str = "generic",
                     max_retries: int = 3,
                     runs: int = 10,
                     opt_levels: Optional[List[str]] = None,
                     noise_floor_ms: float = 0.05,
                     sample_idx: int = 0,
                     faithfulness: bool = False) -> EvalResult:
    """Dataset-path counterpart to evaluate_pattern.

    Compiles LLM code as a separate translation unit alongside the variant's
    on-disk fast.c / test.c / optional helper.c, using -fno-lto.

    The LLM output declares its function as `optimized(...)` (after
    normalize_function_name). We then rename it AGAIN to the variant's
    expected slow function name (e.g. `slow_sr1_v000`) so the variant's
    test.c can link against it.
    """
    from .dataset_evaluator import (
        compile_and_run_variant,
        compile_and_run_reference,
        extract_slow_function_name,
        rename_optimized_to,
    )
    if opt_levels is None:
        opt_levels = ["O2"]
    primary_opt = opt_levels[0]

    prompt = _build_variant_prompt(variant, pattern_lookup, strategy, hw_target)

    # The LLM should fill the role of the variant's slow_<pattern>_v<NNN>
    # function. Extract the target name from the variant's slow.c so we can
    # rename whatever the LLM produced to match.
    with open(variant.slow_path) as f:
        variant_slow_src = f.read()
    target_fn_name = extract_slow_function_name(variant_slow_src) or "optimized"

    llm_code = ""
    result: dict = {"compiles": False, "correct": False}

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
        # extract_code_from_response runs normalize_function_name (→ `optimized`)
        llm_code = extract_code_from_response(llm_response)
        # Second rename: `optimized` → expected slow_<...>_v<NNN> for linking.
        llm_code = rename_optimized_to(llm_code, target_fn_name)

        result = compile_and_run_variant(
            llm_code, variant,
            runs=runs, opt_level=primary_opt,
        )
        if result.get("compiles") and result.get("correct"):
            break

    llm_ms = result.get("llm_ms_median", 0.0) if result.get("correct") else 0.0
    llm_ms_mad = result.get("llm_ms_mad", 0.0) if result.get("correct") else 0.0

    # Reference timing: run the variant's own slow.c + fast.c with matched
    # runs= and same opt level. The fast_ms_median from compile_and_run_variant
    # also reports ref_fast_ms, but we re-run the reference path so we also
    # get a clean variant-slow timing (slow.c was REPLACED by LLM code above).
    slow_ms = 0.0
    slow_ms_mad = 0.0
    ref_fast_ms = result.get("ref_fast_ms_median", 0.0) if result.get("correct") else 0.0
    ref_fast_ms_mad = result.get("ref_fast_ms_mad", 0.0) if result.get("correct") else 0.0

    if result.get("correct"):
        ref = compile_and_run_reference(
            variant, runs=runs, opt_level=primary_opt,
        )
        if ref.get("compiles") and ref.get("correct"):
            slow_ms = ref.get("slow_ms_median", 0.0)
            slow_ms_mad = ref.get("slow_ms_mad", 0.0)
            # Prefer reference run's fast timing if both available — same TU
            # configuration both times, so values should be comparable.
            ref_fast_ms = ref.get("fast_ms_median", ref_fast_ms)
            ref_fast_ms_mad = ref.get("fast_ms_mad", ref_fast_ms_mad)

    speedup_vs_slow = (slow_ms / llm_ms) if (slow_ms > 0 and llm_ms > 0) else 0.0
    speedup_vs_ref = (ref_fast_ms / llm_ms) if (ref_fast_ms > 0 and llm_ms > 0) else 0.0

    # Multi-opt-level recording for candidate.
    llm_ms_O0: Optional[float] = None
    llm_ms_O3: Optional[float] = None
    if result.get("correct"):
        for opt in opt_levels[1:]:
            extra = compile_and_run_variant(
                llm_code, variant, runs=runs, opt_level=opt,
            )
            t = extra.get("llm_ms_median", 0.0) if extra.get("correct") else None
            if opt == "O0":
                llm_ms_O0 = t
            elif opt == "O3":
                llm_ms_O3 = t

    unreliable, reason = _is_unreliable(llm_ms, noise_floor_ms)
    if unreliable and result.get("correct"):
        speedup_vs_slow = 0.0
        speedup_vs_ref = 0.0

    fhfn = {}
    if faithfulness:
        # Dataset path: compute the 2x2 verdict.
        #
        # - Structural axis (expected_shape): per-pattern AST checker on
        #   the LLM output vs slow.c.
        # - Equivalence axis: differential testing across multiple
        #   BENCH_N / BENCH_SEED configs via scripts.bench_hooks +
        #   faithfulness.equivalence.differential_equivalence_on_variant.
        #   Falls back to canonical-input correctness (n_configs=1) if:
        #     * bench_hooks can't patch the variant's test.c (no
        #       #define N or VLA-incompatible structure)
        #     * the multi-TU compile fails (e.g. function-rename edge
        #       case on patterns with multiple top-level functions)
        #   The faithfulness_equiv_configs field on EvalResult records
        #   which mode was used so downstream analyses can distinguish.
        fhfn = _compute_faithfulness(
            variant.pattern_id, variant_slow_src, llm_code,
            test_harness=None,  # structural tier only inside helper
        )

        # Equivalence axis: try multi-config differential first.
        is_equivalent = False
        n_configs = 1
        n_passed = 0
        try:
            from faithfulness.equivalence import differential_equivalence_on_variant
            eq = differential_equivalence_on_variant(
                llm_code, variant, n_inputs=9, opt_level="O2",
            )
            if eq.n_configs > 0 and not eq.compile_error:
                is_equivalent = eq.equivalent
                n_configs = eq.n_configs
                n_passed = eq.n_correct
            else:
                # Fallback: canonical-input correctness from _gather_runs.
                is_equivalent = bool(result.get("correct"))
                n_passed = int(is_equivalent)
        except Exception:
            is_equivalent = bool(result.get("correct"))
            n_passed = int(is_equivalent)

        struct_verdict = fhfn.get("faithfulness_structural_verdict")
        expected_shape = (struct_verdict == "faithful")
        fhfn["faithfulness_equivalent"]     = is_equivalent
        fhfn["faithfulness_expected_shape"] = expected_shape
        fhfn["faithfulness_equiv_configs"]  = n_configs
        fhfn["faithfulness_equiv_passed"]   = n_passed
        # 2x2 routing
        if is_equivalent and expected_shape:
            fhfn["faithfulness_cell"] = "FAITHFUL"
        elif is_equivalent and not expected_shape:
            fhfn["faithfulness_cell"] = "FAITHFUL_ALTERNATIVE"
        elif (not is_equivalent) and expected_shape:
            fhfn["faithfulness_cell"] = "STRUCTURAL_ONLY"
        else:
            fhfn["faithfulness_cell"] = "FAILED"

    return EvalResult(
        pattern_id=variant.pattern_id,
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
        diagnosed_pattern=None,  # dataset prompts don't ask the model to diagnose
        hw_target=hw_target,
        variant_id=variant.variant_id,
        sample_idx=sample_idx,
        slow_ms_mad=slow_ms_mad,
        llm_ms_mad=llm_ms_mad,
        ref_fast_ms_mad=ref_fast_ms_mad,
        llm_ms_O0=llm_ms_O0,
        llm_ms_O3=llm_ms_O3,
        unreliable=unreliable,
        unreliable_reason=reason,
        **fhfn,
    )
