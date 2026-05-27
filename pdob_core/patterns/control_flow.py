# Control-Flow patterns: CF-3 and CF-4.
from ._entry import PatternEntry


CF_PATTERNS = [
    PatternEntry(pattern_id="CF-3", category="Control-Flow", name="Vectorization-Hostile Conditional",
        compiler_difficulty="High",
        description="A noinline function wraps a computation with a runtime guard (always true "
                    "for this data). Verify the invariant once, then use an inline branch-free loop.",
        slow_code="""
static double __attribute__((noinline)) cf3_guarded(double x) {
    return x > 0.0 ? x * x + x * 0.5 : 0.0;
}
void cf3_slow(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) out[i] = cf3_guarded(in[i]);
}""",
        fast_code="""
void cf3_fast(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) out[i] = in[i] * in[i] + in[i] * 0.5;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

static double __attribute__((noinline)) cf3_guarded(double x) {
    return x > 0.0 ? x * x + x * 0.5 : 0.0;
}

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *in  = malloc(n * sizeof(double));
    double *out = malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) in[i] = (double)(i % 100 + 1) * 0.1;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, in, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        double expected = in[i] * in[i] + in[i] * 0.5;
        if (!_bench_close(out[i], expected, 1e-9, 1e-6)) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(in); free(out);
    return 0;
}"""
    ),

    PatternEntry(pattern_id="CF-4", category="Control-Flow", name="Function Pointer Dispatch in Hot Loop",
        compiler_difficulty="High",
        description="Per-element indirect call through a function pointer (or noinline dispatch) "
                    "prevents vectorization. Identify the concrete function at runtime and "
                    "dispatch to an inline tight loop.",
        slow_code="""
typedef double (*TransformFn)(double);
static double __attribute__((noinline)) fn_scale(double x) { return x * 1.5; }
static double __attribute__((noinline)) fn_square(double x) { return x * x; }
static double __attribute__((noinline)) fn_shift(double x)  { return x + 1.0; }
void cf4_slow(double *out, double *in, int n, TransformFn fn) {
    for (int i = 0; i < n; i++) out[i] = fn(in[i]);
}""",
        fast_code="""
void cf4_fast(double *out, double *in, int n, TransformFn fn) {
    if      (fn == fn_scale)  { for (int i=0;i<n;i++) out[i]=in[i]*1.5; }
    else if (fn == fn_square) { for (int i=0;i<n;i++) out[i]=in[i]*in[i]; }
    else if (fn == fn_shift)  { for (int i=0;i<n;i++) out[i]=in[i]+1.0; }
    else                      { for (int i=0;i<n;i++) out[i]=fn(in[i]); }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef double (*TransformFn)(double);
static double __attribute__((noinline)) fn_scale(double x)  { return x * 1.5; }
static double __attribute__((noinline)) fn_square(double x) { return x * x; }
static double __attribute__((noinline)) fn_shift(double x)  { return x + 1.0; }

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *in  = malloc(n * sizeof(double));
    double *out = malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) in[i] = (double)(i % 200 + 1) * 0.05;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, in, n, fn_scale);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (!_bench_close(out[i], in[i] * 1.5, 1e-9, 1e-6)) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(in); free(out);
    return 0;
}"""
    ),
]
