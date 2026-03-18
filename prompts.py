from patterns import PatternEntry

_PORTABILITY_NOTE = (
    "Important: write portable standard C (C99/C11). "
    "Do NOT use x86-specific intrinsics (SSE/AVX/AVX2) or any "
    "#include <immintrin.h> / <xmmintrin.h> / <emmintrin.h>. "
    "Use plain loops that the compiler can auto-vectorize."
)

HW_TARGET_DESCRIPTIONS = {
    "generic":    "a generic CPU with a modern optimizing compiler (-O3)",
    "x86_avx2":   "x86-64 with AVX2 (256-bit SIMD, 8 floats / 4 doubles per register, 64-byte cache lines)",
    "arm_neon":   "ARM with NEON (128-bit SIMD, 4 floats / 2 doubles per register, 64-byte cache lines on Cortex-A, 128-byte on Apple M-series)",
    "arm_apple":  "Apple M-series (ARM NEON, 128-byte cache lines, unified memory, high memory bandwidth)",
    "arm_cortex": "ARM Cortex-A (NEON, 64-byte cache lines)",
    "x86_64":     "x86-64 CPU (64-byte cache lines, SSE4.2 available)",
    "gpu_cuda":   "NVIDIA CUDA GPU (32-thread warps, coalesced global memory, shared memory per block, no branch divergence within a warp)",
    "cpu":        "a standard CPU with -O2 or -O3",
}


def make_prompt_generic(slow_code: str) -> str:
    """Strategy 1: Generic optimization request"""
    return f"""Optimize the following C code for better performance.
Return ONLY the optimized C function. Do not change the function signature.
Rename the function to `optimized`.
{_PORTABILITY_NOTE}

```c
{slow_code}
```"""


def make_prompt_pattern_aware(slow_code: str, pattern: PatternEntry) -> str:
    """Strategy 2: Tell the LLM what pattern category this is"""
    return f"""The following C code contains a performance inefficiency classified as:
Category: {pattern.category}
Pattern: {pattern.name}
Description: {pattern.description}

Optimize this code to eliminate the inefficiency. Rename the function to `optimized`.
Return ONLY the optimized C function.
{_PORTABILITY_NOTE}

```c
{slow_code}
```"""


def make_prompt_taxonomy_guided(slow_code: str) -> str:
    """Strategy 3: Provide the full taxonomy, let LLM diagnose + fix"""
    taxonomy = """
Inefficient Code Pattern Taxonomy:
1. Semantic Redundancy: Loop-invariant computation, recomputable expressions, redundant aggregation
2. Input-Sensitive: Sparse data, distribution skew, early termination, sorted input
3. Control-Flow: Hoistable branches, redundant bounds checks, collapsible loops, generic dispatch
4. Human-Style: Redundant temps, copy-paste duplication, dead code, defensive checks
5. Data Structure: Linear vs hash, repeated allocation, unnecessary copying, AoS vs SoA
6. Algorithmic: Brute force vs DP, repeated sort, naive search, redundant recursion
7. Memory/IO: Allocation in loops, redundant zeroing, heap in hot loop, cache-unfriendly access
"""
    return f"""{taxonomy}

Analyze the following C code. First identify which inefficiency pattern(s) it contains,
then optimize accordingly. Rename the function to `optimized`.
Return ONLY the optimized C function — no explanation, no pattern ID, just the code.
{_PORTABILITY_NOTE}

```c
{slow_code}
```"""


def make_prompt_hardware_target(slow_code: str, target: str) -> str:
    desc = HW_TARGET_DESCRIPTIONS.get(target, target)
    return f"""Optimize the following C code for this specific target: {desc}

Consider the constraints and opportunities specific to this hardware.
Rename the function to `optimized`. Return ONLY the optimized C code.

```c
{slow_code}
```"""


def make_prompt_diagnosis_only(slow_code: str) -> str:
    """Strategy 4: Ask LLM to ONLY diagnose, not optimize"""
    return f"""Analyze the following C code for performance inefficiencies.
Do NOT optimize the code. Instead, identify:
1. What inefficiency pattern(s) are present
2. Which category they belong to (semantic redundancy, input-sensitive,
   control-flow, human-style, data structure, algorithmic, or memory/IO)
3. What specific transformation would fix each inefficiency

```c
{slow_code}
```"""


def build_prompt(pattern: PatternEntry, strategy: str, hw_target: str) -> str:
    if strategy == "generic":
        return make_prompt_generic(pattern.slow_code)
    elif strategy == "pattern-aware":
        return make_prompt_pattern_aware(pattern.slow_code, pattern)
    elif strategy == "taxonomy-guided":
        return make_prompt_taxonomy_guided(pattern.slow_code)
    elif strategy == "hardware-target":
        return make_prompt_hardware_target(pattern.slow_code, hw_target)
    elif strategy == "diagnosis":
        return make_prompt_diagnosis_only(pattern.slow_code)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
