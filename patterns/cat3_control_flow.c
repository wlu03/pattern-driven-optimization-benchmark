// Control flow inefficiencies that depend on runtime data properties.
// Compilers cannot resolve these without observing actual data values at runtime.

#include "../harness/bench_harness.h"

#define N 10000000

// CF-1: Data-Uniform Branch (Homogeneous Batch Dispatch)
// Records in a batch all carry the same runtime type tag in practice,
// but the slow version dispatches to a noinline function per element,
// preventing vectorization and adding per-call overhead regardless of
// optimization level. The compiler cannot inline across the function
// boundary, so SIMD cannot be applied to the compute loop.
// The fast version identifies the batch type with an O(1) first-element
// check, then routes to an inlined, vectorizable loop — eliminating all
// call overhead and allowing the compiler to emit SIMD code.

static double __attribute__((noinline)) cf1_fn_type0(double x) { return x * 2.0 + 1.0; }
static double __attribute__((noinline)) cf1_fn_type1(double x) { return x * x + x; }

void cf1_slow(double *out, double *in, int *type_tags, int n) {
    for (int i = 0; i < n; i++) {
        if (type_tags[i] == 0)
            out[i] = cf1_fn_type0(in[i]);  // noinline: N calls, no vectorization
        else
            out[i] = cf1_fn_type1(in[i]);  // noinline: N calls, no vectorization
    }
}

void cf1_fast(double *out, double *in, int *type_tags, int n) {
    // Identify batch type from first element — batches are homogeneous in practice.
    // Dispatch to an inlined, vectorizable loop: no per-element calls.
    if (type_tags[0] == 0) {
        for (int i = 0; i < n; i++) out[i] = in[i] * 2.0 + 1.0;
    } else {
        for (int i = 0; i < n; i++) out[i] = in[i] * in[i] + in[i];
    }
}

// CF-2: Hot/Cold Path Separation
// Most elements (~99%) follow the hot path (complex computation). The slow
// version routes the hot computation through a noinline function per element,
// preventing vectorization of the loop at any -O level. The rare cold path
// (1% flagged reset to 0) is interleaved, but the noinline hot boundary is
// the primary obstacle — the compiler cannot SIMD-ify any part of the loop.
// The fast version inlines the hot computation and expresses the conditional
// as a branchless ternary, enabling the compiler to emit SIMD (VBLEND/VCMOV).

static double __attribute__((noinline)) cf2_hot(double x) {
    return x * x + x * 0.5 + 1.0;
}

void cf2_slow(double *out, double *in, int *flags, int n) {
    for (int i = 0; i < n; i++) {
        if (flags[i]) {
            out[i] = 0.0;             // Cold: ~1% — cheap, but interleaved
        } else {
            out[i] = cf2_hot(in[i]); // Hot: ~99% — noinline prevents vectorization
        }
    }
}

void cf2_fast(double *out, double *in, int *flags, int n) {
    // Single pass: hot computation inlined, conditional expressed as branchless
    // select — the compiler can emit SIMD with masked stores / VBLEND.
    for (int i = 0; i < n; i++) {
        out[i] = flags[i] ? 0.0 : in[i] * in[i] + in[i] * 0.5 + 1.0;
    }
}

// CF-3: Vectorization-Hostile Redundant Conditional
// A per-element guard is needed in general but is always true for this data.
// The slow version wraps the computation in a noinline function that includes
// the guard, so the compiler must call it N times — a function boundary
// prevents SIMD vectorization and adds per-call overhead at every opt level.
// The fast version verifies the runtime invariant once with a bulk scan,
// then uses an inline branch-free loop the compiler can auto-vectorize,
// eliminating all call overhead and enabling SIMD.

static double __attribute__((noinline)) cf3_guarded(double x) {
    return x > 0.0 ? x * x + x * 0.5 : 0.0;  // Guard inside: safe for any input
}

void cf3_slow(double *out, double *in, int n) {
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded(in[i]);  // N noinline calls: no vectorization possible
}

void cf3_fast(double *out, double *in, int n) {
    // Caller guarantees all-positive: guard is unnecessary.
    // Inline, branch-free loop — the compiler can auto-vectorize with SIMD.
    for (int i = 0; i < n; i++)
        out[i] = in[i] * in[i] + in[i] * 0.5;
}

// CF-4: Function Pointer Dispatch in Hot Loop
// An indirect call through a runtime function pointer cannot be
// devirtualized or inlined by the compiler: the target is unknown at
// compile time. Call overhead and lost inlining accumulate over millions
// of iterations. The fast version identifies the concrete target at
// runtime and dispatches to a direct inlined loop, eliminating
// the per-element indirect branch entirely.

typedef double (*TransformFn)(double);

static double __attribute__((noinline)) fn_relu(double x)   { return x > 0.0 ? x : 0.0; }
static double __attribute__((noinline)) fn_square(double x) { return x * x; }
static double __attribute__((noinline)) fn_scale(double x)  { return x * 1.5; }

typedef struct { TransformFn fn; } Transformer;

void cf4_slow(double *out, double *in, int n, Transformer *t) {
    for (int i = 0; i < n; i++) {
        out[i] = t->fn(in[i]);  // Indirect call per element: no inlining
    }
}

void cf4_fast(double *out, double *in, int n, Transformer *t) {
    // Identify concrete target at runtime, dispatch to inlined tight loop
    if (t->fn == fn_relu) {
        for (int i = 0; i < n; i++) out[i] = in[i] > 0.0 ? in[i] : 0.0;
    } else if (t->fn == fn_square) {
        for (int i = 0; i < n; i++) out[i] = in[i] * in[i];
    } else if (t->fn == fn_scale) {
        for (int i = 0; i < n; i++) out[i] = in[i] * 1.5;
    } else {
        for (int i = 0; i < n; i++) out[i] = t->fn(in[i]);  // Fallback
    }
}


void run_control_flow(void) {
    srand(42);
    double *A = malloc(N * sizeof(double));
    double *out_slow = malloc(N * sizeof(double));
    double *out_fast = malloc(N * sizeof(double));

    // All positive: required for CF-3 to exercise the always-true branch
    fill_random_double(A, N, 0.5, 10.0);

    // CF-1: Homogeneous type tags — all 0 in this batch
    {
        int *tags = malloc(N * sizeof(int));
        for (int i = 0; i < N; i++) tags[i] = 0;

        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) cf1_slow(out_slow, A, tags, N);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) cf1_fast(out_fast, A, tags, N);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("CF-1", "Data-Uniform Batch Dispatch", ms_slow, ms_fast, ok);
        printf("[CF-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(tags);
    }

    // CF-2: Hot/cold separation — ~1% of flags set
    {
        int *flags = calloc(N, sizeof(int));
        for (int i = 0; i < N; i++) {
            if (rand() % 100 == 0) flags[i] = 1;
        }

        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) cf2_slow(out_slow, A, flags, N);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) cf2_fast(out_fast, A, flags, N);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("CF-2", "Hot/Cold Path Separation", ms_slow, ms_fast, ok);
        printf("[CF-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(flags);
    }

    // CF-3: Always-true conditional preventing vectorization
    // A is already all-positive (filled with [0.5, 10.0])
    {
        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) cf3_slow(out_slow, A, N);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) cf3_fast(out_fast, A, N);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("CF-3", "Vectorization-Hostile Conditional", ms_slow, ms_fast, ok);
        printf("[CF-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // CF-4: Function pointer dispatch — fn_scale used throughout
    {
        Transformer t_obj;
        t_obj.fn = fn_scale;

        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) cf4_slow(out_slow, A, N, &t_obj);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) cf4_fast(out_fast, A, N, &t_obj);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("CF-4", "Function Pointer Dispatch", ms_slow, ms_fast, ok);
        printf("[CF-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    free(A); free(out_slow); free(out_fast);
}
