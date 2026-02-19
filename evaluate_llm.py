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
    python3 evaluate_llm.py --model claude-sonnet --strategy pattern-aware
    python3 evaluate_llm.py --model deepseek-v3 --strategy taxonomy-guided
"""

import json
import os
import subprocess
import tempfile
import time
import argparse
import csv
from dataclasses import dataclass, field, asdict
from typing import Optional

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
                     call_llm_fn) -> EvalResult:
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

def main():
    parser = argparse.ArgumentParser(description="LLM Code Optimization Evaluator")
    parser.add_argument("--model", default="gpt-4o",
                        help="Model to evaluate")
    parser.add_argument("--strategy", default="generic",
                        choices=["generic", "pattern-aware", "taxonomy-guided", "diagnosis"],
                        help="Prompting strategy")
    parser.add_argument("--output", default="results.csv",
                        help="Output CSV file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompts without calling LLM")
    args = parser.parse_args()

    if args.dry_run:
        # Just show what prompts would be generated
        for p in PATTERNS:
            if args.strategy == "generic":
                prompt = make_prompt_generic(p.slow_code)
            elif args.strategy == "pattern-aware":
                prompt = make_prompt_pattern_aware(p.slow_code, p)
            elif args.strategy == "taxonomy-guided":
                prompt = make_prompt_taxonomy_guided(p.slow_code)
            else:
                prompt = make_prompt_diagnosis_only(p.slow_code)

            print(f"\n{'='*60}")
            print(f"Pattern: {p.pattern_id} - {p.name}")
            print(f"{'='*60}")
            print(prompt)
        return

    print(f"Evaluating {len(PATTERNS)} patterns with model={args.model}, strategy={args.strategy}")
    print("(Implement call_llm_fn with your API key to run actual evaluation)")


if __name__ == "__main__":
    main()
