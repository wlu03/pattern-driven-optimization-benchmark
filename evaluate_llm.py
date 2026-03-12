"""
LLM Evaluation Framework for Pattern-Driven Code Optimization Benchmark

This script:
1. Extracts each SLOW function from the benchmark
2. Sends it to an LLM with various prompting strategies
3. Compiles the LLM output
4. Runs it against test cases
5. Measures speedup vs. the slow version and the hand-optimized version
6. Records results per pattern category

Usage:
    python3 evaluate_llm.py --model gpt-4o --strategy generic
    python3 evaluate_llm.py --model claude-sonnet-4-6 --strategy pattern-aware
    python3 evaluate_llm.py --model deepseek-v3 --strategy taxonomy-guided
    python3 evaluate_llm.py --all-models --strategy generic --output results.csv
    python3 evaluate_llm.py --list-models
    python3 evaluate_llm.py --dry-run --model gpt-4o --strategy generic

Requires:
    pip install anthropic openai google-generativeai pyyaml
"""

import json
import os
import subprocess
import tempfile
import time
import argparse
import csv
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable

# ── Pattern Registry ──────────────────────────────────────────
@dataclass
class PatternEntry:
    pattern_id: str          # e.g., "SR-1"
    category: str            # e.g., "Semantic Redundancy"
    name: str                # e.g., "Loop-Invariant Semantic Computation"
    slow_code: str           # The inefficient C code
    fast_code: str           # Hand-optimized reference
    test_harness: str        # Code to call and verify the function
    compiler_difficulty: str  # "Low", "Medium", "High", "Very High"
    description: str         # What the inefficiency is

# All 28 patterns
PATTERNS = [
    # ── CATEGORY 1: Semantic Redundancy ──
    PatternEntry(
        pattern_id="SR-1",
        category="Semantic Redundancy",
        name="Loop-Invariant Semantic Computation",
        compiler_difficulty="High",
        description="Expression `A[i] + B[i] * delta` is accumulated in a loop. "
                    "The multiply by delta can be factored out as a single multiply "
                    "after accumulating B separately.",
        slow_code="""
double sr1_slow(double *A, double *B, int n, double delta) {
    double t = 0.0;
    for (int i = 0; i < n; i++) {
        t += A[i] + B[i] * delta;
    }
    return t;
}""",
        fast_code="""
double sr1_fast(double *A, double *B, int n, double delta) {
    double sumA = 0.0, sumB = 0.0;
    for (int i = 0; i < n; i++) {
        sumA += A[i];
        sumB += B[i];
    }
    return sumA + sumB * delta;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *A = malloc(n * sizeof(double));
    double *B = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) {
        A[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);
        B[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double result = optimized(A, B, n, 3.14159);
    clock_gettime(CLOCK_MONOTONIC, &end);

    double ms = (end.tv_sec - start.tv_sec) * 1000.0
              + (end.tv_nsec - start.tv_nsec) / 1e6;

    // Expected result (computed with slow version)
    double expected = 0.0;
    for (int i = 0; i < n; i++) expected += A[i] + B[i] * 3.14159;
    double err = fabs(result - expected) / fmax(fabs(expected), 1e-12);

    printf("result=%.10f time_ms=%.4f correct=%d\\n", result, ms, err < 1e-6);
    free(A); free(B);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="SR-2",
        category="Semantic Redundancy",
        name="Recomputable Expression Decomposition",
        compiler_difficulty="High",
        description="Expression `alpha*X[i]*X[i] + beta*Y[i] + alpha*beta` can be "
                    "decomposed into separate accumulators for X^2 and Y sums.",
        slow_code="""
double sr2_slow(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] * X[i] + beta * Y[i] + alpha * beta;
    }
    return result;
}""",
        fast_code="""
double sr2_fast(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0.0, sumY = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (double)n * alpha * beta;
}""",
        test_harness=""  # Similar structure, omitted for brevity
    ),

    PatternEntry(
        pattern_id="SR-3",
        category="Semantic Redundancy",
        name="Redundant Aggregation Recomputation",
        compiler_difficulty="Very High",
        description="Recomputing a running average from scratch each iteration "
                    "(O(n^2)) instead of maintaining a running sum (O(n)).",
        slow_code="""
void sr3_slow(double *data, double *running_avg, int n) {
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j <= i; j++) {
            sum += data[j];
        }
        running_avg[i] = sum / (i + 1);
    }
}""",
        fast_code="""
void sr3_fast(double *data, double *running_avg, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        running_avg[i] = sum / (i + 1);
    }
}""",
        test_harness=""
    ),

    PatternEntry(
        pattern_id="SR-4",
        category="Semantic Redundancy",
        name="Invariant Function Call in Loop",
        compiler_difficulty="High",
        description="A pure function with loop-invariant arguments is called "
                    "every iteration. Compiler can't hoist across TU boundaries.",
        slow_code="""
#include <math.h>
double expensive_lookup(int key) {
    double r = 0.0;
    for (int i = 0; i < 100; i++)
        r += sin((double)(key+i)) * cos((double)(key-i));
    return r;
}
void sr4_slow(double *arr, int n, int config_key) {
    for (int i = 0; i < n; i++) {
        double factor = expensive_lookup(config_key);
        arr[i] *= factor;
    }
}""",
        fast_code="""
#include <math.h>
double expensive_lookup(int key) {
    double r = 0.0;
    for (int i = 0; i < 100; i++)
        r += sin((double)(key+i)) * cos((double)(key-i));
    return r;
}
void sr4_fast(double *arr, int n, int config_key) {
    double factor = expensive_lookup(config_key);
    for (int i = 0; i < n; i++) arr[i] *= factor;
}""",
        test_harness=""
    ),

    PatternEntry(
        pattern_id="SR-5",
        category="Semantic Redundancy",
        name="Algebraic Strength Reduction",
        compiler_difficulty="Medium",
        description="Using sqrt for distance when only relative comparison needed. "
                    "Squared distance avoids expensive sqrt.",
        slow_code="""
#include <math.h>
void sr5_slow(double *dist, double *X, double *Y, int n, double cx, double cy) {
    for (int i = 0; i < n; i++) {
        dist[i] = sqrt((X[i]-cx)*(X[i]-cx) + (Y[i]-cy)*(Y[i]-cy));
    }
}""",
        fast_code="""
void sr5_fast(double *dist, double *X, double *Y, int n, double cx, double cy) {
    for (int i = 0; i < n; i++) {
        double dx = X[i]-cx, dy = Y[i]-cy;
        dist[i] = dx*dx + dy*dy;
    }
}""",
        test_harness=""
    ),

    # ── CATEGORY 2: Input-Sensitive ──
    PatternEntry(
        pattern_id="IS-1",
        category="Input-Sensitive Inefficiency",
        name="Sparse Data Redundancy",
        compiler_difficulty="Very High",
        description="Weight update `w[k][j] += delta[j]*layer[k]` processes all "
                    "elements even when 90% are zero. Add zero-skip guards.",
        slow_code="""
void is1_slow(double *w, double *delta, double *layer, int nj, int nk) {
    for (int k = 0; k < nk; k++) {
        for (int j = 0; j < nj; j++) {
            double new_dw = delta[j] * layer[k];
            w[k * nj + j] += new_dw;
        }
    }
}""",
        fast_code="""
void is1_fast(double *w, double *delta, double *layer, int nj, int nk) {
    for (int k = 0; k < nk; k++) {
        if (layer[k] == 0.0) continue;
        for (int j = 0; j < nj; j++) {
            if (delta[j] == 0.0) continue;
            w[k * nj + j] += delta[j] * layer[k];
        }
    }
}""",
        test_harness=""
    ),

    PatternEntry(
        pattern_id="IS-2",
        category="Input-Sensitive Inefficiency",
        name="Data Distribution Skew",
        compiler_difficulty="Very High",
        description="Expensive gradient clipping applied to all values when 99% "
                    "are within threshold. Fast path for common case.",
        slow_code="""
#include <math.h>
void is2_slow(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        double sign = (val >= 0) ? 1.0 : -1.0;
        double abs_val = fabs(val);
        if (abs_val > thresh)
            out[i] = sign * (thresh + log(1.0 + abs_val - thresh));
        else
            out[i] = val;
    }
}""",
        fast_code="""
#include <math.h>
void is2_fast(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        if (fabs(val) <= thresh) { out[i] = val; continue; }
        double sign = (val >= 0) ? 1.0 : -1.0;
        out[i] = sign * (thresh + log(1.0 + fabs(val) - thresh));
    }
}""",
        test_harness=""
    ),

    PatternEntry(
        pattern_id="IS-3",
        category="Input-Sensitive Inefficiency",
        name="Early Termination",
        compiler_difficulty="High",
        description="Counting all violations when only need to know if any exist. "
                    "Early return on first violation.",
        slow_code="""
int is3_slow(double *arr, int n, double threshold) {
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] > threshold) count++;
    }
    return count == 0;
}""",
        fast_code="""
int is3_fast(double *arr, int n, double threshold) {
    for (int i = 0; i < n; i++) {
        if (arr[i] > threshold) return 0;
    }
    return 1;
}""",
        test_harness=""
    ),

    PatternEntry(
        pattern_id="IS-4",
        category="Input-Sensitive Inefficiency",
        name="Sorted Input Exploitation",
        compiler_difficulty="Very High",
        description="Always running O(n log n) sort even when input is already sorted. "
                    "Check sorted first in O(n).",
        slow_code="""
#include <stdlib.h>
static int cmp_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}
void is4_slow(int *arr, int n) {
    qsort(arr, n, sizeof(int), cmp_int);
}""",
        fast_code="""
#include <stdlib.h>
static int cmp_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}
void is4_fast(int *arr, int n) {
    int sorted = 1;
    for (int i = 1; i < n; i++) {
        if (arr[i] < arr[i-1]) { sorted = 0; break; }
    }
    if (!sorted) qsort(arr, n, sizeof(int), cmp_int);
}""",
        test_harness=""
    ),

    # ── CATEGORY 3: Control-Flow ──
    PatternEntry(pattern_id="CF-1", category="Control-Flow", name="Loop-Invariant Conditional",
        compiler_difficulty="Medium",
        description="Branch on `mode` checked every iteration. Hoist outside loop.",
        slow_code="""
void cf1_slow(double *out, double *A, double *B, int n, int mode) {
    for (int i = 0; i < n; i++) {
        if (mode == 1) out[i] = A[i] + B[i];
        else if (mode == 2) out[i] = A[i] * B[i];
        else out[i] = A[i] - B[i];
    }
}""",
        fast_code="""
void cf1_fast(double *out, double *A, double *B, int n, int mode) {
    if (mode == 1) { for (int i = 0; i < n; i++) out[i] = A[i] + B[i]; }
    else if (mode == 2) { for (int i = 0; i < n; i++) out[i] = A[i] * B[i]; }
    else { for (int i = 0; i < n; i++) out[i] = A[i] - B[i]; }
}""",
        test_harness=""
    ),

    PatternEntry(pattern_id="CF-2", category="Control-Flow", name="Redundant Bounds Checking",
        compiler_difficulty="Medium",
        description="Checking `i >= 0 && i < rows && j >= 0 && j < cols` inside nested loops "
                    "that already guarantee bounds.",
        slow_code="""
void cf2_slow(double *mat, int rows, int cols, double *sums) {
    for (int i = 0; i < rows; i++) {
        sums[i] = 0.0;
        for (int j = 0; j < cols; j++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols)
                sums[i] += mat[i * cols + j];
        }
    }
}""",
        fast_code="""
void cf2_fast(double *mat, int rows, int cols, double *sums) {
    for (int i = 0; i < rows; i++) {
        sums[i] = 0.0;
        for (int j = 0; j < cols; j++)
            sums[i] += mat[i * cols + j];
    }
}""",
        test_harness=""
    ),

    PatternEntry(pattern_id="CF-3", category="Control-Flow", name="Unnecessary Loop Nesting",
        compiler_difficulty="Low",
        description="Nested loops over flat iteration space. Collapse into single loop.",
        slow_code="""
void cf3_slow(double *mat, int rows, int cols, double scalar) {
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            mat[i * cols + j] *= scalar;
}""",
        fast_code="""
void cf3_fast(double *mat, int rows, int cols, double scalar) {
    int total = rows * cols;
    for (int i = 0; i < total; i++) mat[i] *= scalar;
}""",
        test_harness=""
    ),

    PatternEntry(pattern_id="CF-4", category="Control-Flow", name="Premature Generalization",
        compiler_difficulty="Medium",
        description="Switch/dispatch inside hot loop when operation is invariant. "
                    "Resolve dispatch once outside loop.",
        slow_code="""
typedef enum { OP_ADD, OP_MUL, OP_SUB } OpType;
double apply_op(OpType op, double a, double b) {
    switch(op) {
        case OP_ADD: return a + b;
        case OP_MUL: return a * b;
        case OP_SUB: return a - b;
        default: return 0.0;
    }
}
void cf4_slow(double *out, double *A, double *B, int n, OpType op) {
    for (int i = 0; i < n; i++) out[i] = apply_op(op, A[i], B[i]);
}""",
        fast_code="""
typedef enum { OP_ADD, OP_MUL, OP_SUB } OpType;
void cf4_fast(double *out, double *A, double *B, int n, OpType op) {
    switch(op) {
        case OP_ADD: for (int i=0;i<n;i++) out[i]=A[i]+B[i]; break;
        case OP_MUL: for (int i=0;i<n;i++) out[i]=A[i]*B[i]; break;
        case OP_SUB: for (int i=0;i<n;i++) out[i]=A[i]-B[i]; break;
    }
}""",
        test_harness=""
    ),

    # ── CATEGORY 4-7: Abbreviated (same structure) ──
    # Full entries follow same pattern... DS-1 through MI-4
    # (See the C files for complete implementations)

    PatternEntry(pattern_id="DS-4", category="Data Structure", name="AoS vs SoA Cache Access",
        compiler_difficulty="Very High",
        description="Array of Structures causes 64-byte stride when accessing one field. "
                    "Structure of Arrays gives sequential 8-byte stride.",
        slow_code="""
typedef struct { double x,y,z,vx,vy,vz,mass,charge; } Particle;
double ds4_slow(Particle *p, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += p[i].mass;
    return total;
}""",
        fast_code="""
double ds4_fast(double *mass, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}""",
        test_harness=""
    ),

    PatternEntry(pattern_id="AL-1", category="Algorithmic", name="Recursive vs DP Fibonacci",
        compiler_difficulty="Very High",
        description="O(2^n) recursive Fibonacci vs O(n) iterative. "
                    "Compiler cannot transform recursion into DP.",
        slow_code="""
long long al1_slow(int n) {
    if (n <= 1) return n;
    return al1_slow(n-1) + al1_slow(n-2);
}""",
        fast_code="""
long long al1_fast(int n) {
    if (n <= 1) return n;
    long long a=0, b=1;
    for (int i=2; i<=n; i++) { long long t=a+b; a=b; b=t; }
    return b;
}""",
        test_harness=""
    ),

    PatternEntry(pattern_id="MI-4", category="Memory/IO", name="Column vs Row Major Access",
        compiler_difficulty="Medium",
        description="Column-major traversal in row-major C causes cache misses. "
                    "Swap loop order for sequential access.",
        slow_code="""
void mi4_slow(double *mat, int rows, int cols) {
    for (int j = 0; j < cols; j++)
        for (int i = 0; i < rows; i++)
            mat[i * cols + j] *= 2.0;
}""",
        fast_code="""
void mi4_fast(double *mat, int rows, int cols) {
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            mat[i * cols + j] *= 2.0;
}""",
        test_harness=""
    ),
]


def make_prompt_generic(slow_code: str) -> str:
    """Strategy 1: Generic optimization request"""
    return f"""Optimize the following C code for better performance.
Return ONLY the optimized C function. Do not change the function signature.
Rename the function to `optimized`.

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
Return the pattern ID and the optimized function.

```c
{slow_code}
```"""

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

def compile_and_run(code: str, test_harness: str, timeout: int = 30) -> dict:
    """Compile LLM-generated code with test harness, run, parse output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "test.c")
        bin_path = os.path.join(tmpdir, "test")

        full_code = test_harness.replace("// LLM_CODE_HERE", code)
        with open(src_path, "w") as f:
            f.write(full_code)

        # Compile
        result = subprocess.run(
            ["gcc", "-O0", "-o", bin_path, src_path, "-lm"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {"compiles": False, "error": result.stderr}

        # Run
        result = subprocess.run(
            [bin_path], capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return {"compiles": True, "correct": False, "error": "runtime error"}

        # Parse output: "result=X time_ms=Y correct=Z"
        output = result.stdout.strip()
        parts = dict(p.split("=") for p in output.split() if "=" in p)

        return {
            "compiles": True,
            "correct": parts.get("correct", "0") == "1",
            "time_ms": float(parts.get("time_ms", 0)),
            "result": parts.get("result", "")
        }


def evaluate_pattern(pattern: PatternEntry, model: str, strategy: str,
                     call_llm_fn, hw_target: str = "generic") -> EvalResult:
    """Evaluate a single pattern with a specific model and strategy."""

    # Select prompt
    if strategy == "generic":
        prompt = make_prompt_generic(pattern.slow_code)
    elif strategy == "pattern-aware":
        prompt = make_prompt_pattern_aware(pattern.slow_code, pattern)
    elif strategy == "taxonomy-guided":
        prompt = make_prompt_taxonomy_guided(pattern.slow_code)
    elif strategy == "diagnosis":
        prompt = make_prompt_diagnosis_only(pattern.slow_code)
    elif strategy == "hardware-target":
        prompt = make_prompt_hardware_target(pattern.slow_code, hw_target)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Call LLM
    llm_response = call_llm_fn(prompt, model)

    # Extract code from response
    llm_code = extract_code_from_response(llm_response)

    # Compile and test
    if pattern.test_harness:
        result = compile_and_run(llm_code, pattern.test_harness)
    else:
        result = {"compiles": False, "correct": False, "time_ms": 0}

    return EvalResult(
        pattern_id=pattern.pattern_id,
        model=model,
        strategy=strategy,
        llm_code=llm_code,
        compiles=result.get("compiles", False),
        correct=result.get("correct", False),
        slow_ms=0,  # Filled in by benchmark runner
        llm_ms=result.get("time_ms", 0),
        ref_fast_ms=0,
        speedup_vs_slow=0,
        speedup_vs_ref=0,
        hw_target=hw_target,
    )


def extract_code_from_response(response: str) -> str:
    """Extract C code from LLM markdown response."""
    if "```c" in response:
        start = response.index("```c") + 4
        end = response.index("```", start)
        return response[start:end].strip()
    if "```" in response:
        start = response.index("```") + 3
        end = response.index("```", start)
        return response[start:end].strip()
    return response.strip()

# ── Model config loading ────────────────────────────────────────────────────

def load_model_config(config_path: str = "models.yaml") -> dict:
    """Load models.yaml and return {model_id: model_cfg} plus defaults."""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    defaults = cfg.get("defaults", {})
    models = {}
    for m in cfg.get("models", []):
        merged = {**defaults, **m}   # per-model overrides defaults
        models[m["id"]] = merged
    return models


# ── Provider implementations ────────────────────────────────────────────────

def _call_anthropic(prompt: str, model_cfg: dict) -> str:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed: pip install anthropic")

    api_key = os.environ.get(model_cfg["api_key_env"])
    if not api_key:
        raise RuntimeError(f"Environment variable {model_cfg['api_key_env']} is not set")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model_cfg["model_name"],
        max_tokens=model_cfg.get("max_tokens", 2048),
        temperature=model_cfg.get("temperature", 0.2),
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_openai(prompt: str, model_cfg: dict) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")

    api_key = os.environ.get(model_cfg.get("api_key_env", ""))
    if not api_key:
        raise RuntimeError(f"Environment variable {model_cfg.get('api_key_env')} is not set")

    kwargs = {"api_key": api_key}
    if model_cfg.get("base_url"):
        kwargs["base_url"] = model_cfg["base_url"]

    client = OpenAI(**kwargs)

    # o-series reasoning models don't support system prompts or low temp
    create_kwargs = dict(
        model=model_cfg["model_name"],
        messages=[{"role": "user", "content": prompt}],
    )
    if not model_cfg["model_name"].startswith("o"):
        create_kwargs["temperature"] = model_cfg.get("temperature", 0.2)
        create_kwargs["max_tokens"] = model_cfg.get("max_tokens", 2048)
    else:
        create_kwargs["max_completion_tokens"] = model_cfg.get("max_tokens", 4096)

    response = client.chat.completions.create(**create_kwargs)
    return response.choices[0].message.content


def _call_ollama(prompt: str, model_cfg: dict) -> str:
    """Ollama local server — OpenAI-compatible, no auth required."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")

    base_url = model_cfg.get("base_url", "http://localhost:11434/v1")
    client = OpenAI(api_key="ollama", base_url=base_url)  # key value is ignored by Ollama
    response = client.chat.completions.create(
        model=model_cfg["model_name"],
        messages=[{"role": "user", "content": prompt}],
        temperature=model_cfg.get("temperature", 0.2),
        max_tokens=model_cfg.get("max_tokens", 2048),
    )
    return response.choices[0].message.content


def _call_google(prompt: str, model_cfg: dict) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai not installed: pip install google-generativeai")

    api_key = os.environ.get(model_cfg["api_key_env"])
    if not api_key:
        raise RuntimeError(f"Environment variable {model_cfg['api_key_env']} is not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_cfg["model_name"])
    gen_config = genai.GenerationConfig(
        temperature=model_cfg.get("temperature", 0.2),
        max_output_tokens=model_cfg.get("max_tokens", 2048),
    )
    response = model.generate_content(prompt, generation_config=gen_config)
    return response.text


_PROVIDER_FNS = {
    "anthropic":     _call_anthropic,
    "openai":        _call_openai,
    "openai_compat": _call_openai,   # same client, base_url differs (Together, Groq, DeepSeek…)
    "google":        _call_google,
    "ollama":        _call_ollama,   # local Ollama server, no API key
}


def make_call_llm_fn(model_cfg: dict, retries: int = 2) -> Callable[[str, str], str]:
    """Return a call_llm_fn(prompt, model_id) closure for the given config entry."""
    provider = model_cfg.get("provider", "openai")
    provider_fn = _PROVIDER_FNS.get(provider)
    if provider_fn is None:
        raise ValueError(f"Unknown provider '{provider}'. Supported: {list(_PROVIDER_FNS)}")

    def call_llm(prompt: str, _model_id: str) -> str:
        last_err = None
        for attempt in range(retries + 1):
            try:
                return provider_fn(prompt, model_cfg)
            except Exception as e:
                last_err = e
                if attempt < retries:
                    wait = 2 ** attempt
                    print(f"  [retry {attempt+1}/{retries} in {wait}s] {e}", file=sys.stderr)
                    time.sleep(wait)
        raise RuntimeError(f"All {retries+1} attempts failed: {last_err}") from last_err

    return call_llm


# ── Main ────────────────────────────────────────────────────────────────────

def _build_prompt(pattern: "PatternEntry", strategy: str, hw_target: str) -> str:
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


def _write_results(results: list, output_path: str) -> None:
    if not results:
        return
    fieldnames = list(asdict(results[0]).keys())
    write_header = not os.path.exists(output_path)
    with open(output_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))


def main():
    parser = argparse.ArgumentParser(description="LLM Code Optimization Evaluator")
    parser.add_argument("--config", default="models.yaml",
                        help="Path to models.yaml config file")
    parser.add_argument("--model", default=None,
                        help="Model ID to evaluate (from models.yaml)")
    parser.add_argument("--all-models", action="store_true",
                        help="Evaluate all models defined in models.yaml")
    parser.add_argument("--list-models", action="store_true",
                        help="List available models from config and exit")
    parser.add_argument("--strategy", default="generic",
                        choices=["generic", "pattern-aware", "taxonomy-guided",
                                 "diagnosis", "hardware-target"],
                        help="Prompting strategy")
    parser.add_argument("--target", default="generic",
                        choices=list(HW_TARGET_DESCRIPTIONS.keys()),
                        help="Hardware target (for hardware-target strategy)")
    parser.add_argument("--patterns", default=None,
                        help="Comma-separated pattern IDs to evaluate (e.g. SR-1,CF-2). "
                             "Default: all patterns with a test harness.")
    parser.add_argument("--output", default="results.csv",
                        help="Output CSV file (appended to if it already exists)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompts without calling any LLM")
    args = parser.parse_args()

    # Load config
    models_cfg = load_model_config(args.config)

    # --list-models
    if args.list_models:
        print(f"{'ID':<30} {'Provider':<15} {'Auth / Endpoint':<30} Description")
        print("-" * 100)
        current_provider = None
        for mid, mcfg in models_cfg.items():
            provider = mcfg.get("provider", "")
            # Print a section header when the provider group changes
            if provider != current_provider:
                section = {
                    "anthropic":     "── Anthropic ──",
                    "openai":        "── OpenAI ──",
                    "openai_compat": "── OpenAI-compatible (Together AI / Groq / DeepSeek) ──",
                    "google":        "── Google ──",
                    "ollama":        "── Ollama (local) ──",
                }.get(provider, f"── {provider} ──")
                print(f"\n{section}")
                current_provider = provider

            if provider == "ollama":
                auth_info = mcfg.get("base_url", "http://localhost:11434/v1")
            else:
                key_var = mcfg.get("api_key_env", "")
                key_set = "✓" if os.environ.get(key_var) else "✗ not set"
                auth_info = f"{key_var}={key_set}"

            print(f"  {mid:<28} {provider:<15} {auth_info:<30} {mcfg.get('description','')}")
        return

    # Resolve which models to run
    if args.all_models:
        model_ids = list(models_cfg.keys())
    elif args.model:
        if args.model not in models_cfg:
            print(f"ERROR: model '{args.model}' not found in {args.config}. "
                  f"Use --list-models to see available models.", file=sys.stderr)
            sys.exit(1)
        model_ids = [args.model]
    else:
        parser.print_help()
        print("\nProvide --model <id> or --all-models (or --list-models to see options).",
              file=sys.stderr)
        sys.exit(1)

    # Filter patterns
    active_patterns = [p for p in PATTERNS if p.test_harness.strip()]
    if args.patterns:
        wanted = {x.strip() for x in args.patterns.split(",")}
        active_patterns = [p for p in active_patterns if p.pattern_id in wanted]
    if not active_patterns:
        print("No patterns match the filter (check --patterns or that test_harness is set).",
              file=sys.stderr)
        sys.exit(1)

    # --dry-run: print prompts and exit
    if args.dry_run:
        for p in active_patterns:
            prompt = _build_prompt(p, args.strategy, args.target)
            print(f"\n{'='*60}")
            print(f"Pattern: {p.pattern_id} — {p.name}")
            print(f"Strategy: {args.strategy}  |  Models: {', '.join(model_ids)}")
            print(f"{'='*60}")
            print(prompt)
        return

    # Run evaluation
    total = len(model_ids) * len(active_patterns)
    print(f"Evaluating {len(active_patterns)} patterns × {len(model_ids)} model(s) "
          f"= {total} runs  [strategy={args.strategy}]")
    print(f"Output → {args.output}\n")

    all_results = []
    run_idx = 0
    for model_id in model_ids:
        mcfg = models_cfg[model_id]
        retries = mcfg.get("retries", 2)
        try:
            call_llm_fn = make_call_llm_fn(mcfg, retries=retries)
        except Exception as e:
            print(f"[SKIP] {model_id}: {e}", file=sys.stderr)
            continue

        for pattern in active_patterns:
            run_idx += 1
            print(f"[{run_idx:>3}/{total}] {model_id:<25} {pattern.pattern_id:<6} ", end="", flush=True)
            t0 = time.time()
            try:
                result = evaluate_pattern(pattern, model_id, args.strategy,
                                          call_llm_fn, hw_target=args.target)
                elapsed = time.time() - t0
                status = "OK" if result.compiles and result.correct else \
                         ("COMPILE_ERR" if not result.compiles else "WRONG")
                print(f"{status:<12} {elapsed:.1f}s  llm_ms={result.llm_ms:.1f}")
                all_results.append(result)
            except Exception as e:
                elapsed = time.time() - t0
                print(f"ERROR        {elapsed:.1f}s  {e}", file=sys.stderr)

        # Flush after each model so partial results are saved
        _write_results(all_results, args.output)
        all_results = []

    # Summary
    print(f"\nDone. Results appended to {args.output}")


if __name__ == "__main__":
    main()
