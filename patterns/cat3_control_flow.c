// Control flow inefficiencies that depend on runtime data properties.
// Compilers cannot resolve these without observing actual data values at runtime.

#include "../harness/bench_harness.h"

#define N 10000000

// CF-1: Data-Uniform Branch (Homogeneous Batch Dispatch)
// Records in a batch all carry the same runtime type tag in practice,
// but the slow version loads and checks each tag individually per element.
// The compiler must conservatively read type_tags[i] every iteration —
// it cannot prove uniformity from static analysis alone.
// The fast version detects homogeneity with a single runtime scan,
// then routes to a specialized branch-free, vectorizable loop.

void cf1_slow(double *out, double *in, int *type_tags, int n) {
    for (int i = 0; i < n; i++) {
        if (type_tags[i] == 0) {
            out[i] = in[i] * 2.0 + 1.0;
        } else {
            out[i] = in[i] * in[i] + in[i];
        }
    }
}

void cf1_fast(double *out, double *in, int *type_tags, int n) {
    // Single pass: detect whether the batch is homogeneous at runtime
    int tag = type_tags[0], uniform = 1;
    for (int i = 1; i < n; i++) {
        if (type_tags[i] != tag) { uniform = 0; break; }
    }
    if (uniform && tag == 0) {
        for (int i = 0; i < n; i++) out[i] = in[i] * 2.0 + 1.0;
    } else if (uniform) {
        for (int i = 0; i < n; i++) out[i] = in[i] * in[i] + in[i];
    } else {
        // Mixed batch: fallback to per-element dispatch
        for (int i = 0; i < n; i++)
            out[i] = (type_tags[i] == 0) ? in[i] * 2.0 + 1.0 : in[i] * in[i] + in[i];
    }
}

// CF-2: Hot/Cold Path Separation
// A rarely-triggered flag causes error-handling code to be interleaved
// with the hot computation path every iteration. The compiler cannot prove
// flags[i] is almost always 0 — it's runtime data. The mixed branch
// disrupts vectorization of the common case.
// The fast version separates concerns: one clean vectorizable pass for the
// hot path, then a sparse fixup pass for the rare flagged entries.

void cf2_slow(double *out, double *in, int *flags, int n) {
    for (int i = 0; i < n; i++) {
        if (flags[i]) {                                   // Rare: ~1% of elements
            out[i] = 0.0;                                 // Error/reset path
        } else {
            out[i] = in[i] * in[i] + in[i] * 0.5 + 1.0; // Hot path
        }
    }
}

void cf2_fast(double *out, double *in, int *flags, int n) {
    // Hot pass: branch-free, auto-vectorizable
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * in[i] + in[i] * 0.5 + 1.0;
    }
    // Cold pass: fix up the rare flagged entries
    for (int i = 0; i < n; i++) {
        if (flags[i]) out[i] = 0.0;
    }
}

// CF-3: Vectorization-Hostile Redundant Conditional
// A per-element conditional on a runtime property that is always true
// for the given data prevents the compiler from emitting SIMD code.
// The compiler cannot prove in[i] > 0.0 from static analysis — the data
// could be anything. The fast version verifies the property with one
// runtime scan, then uses a branch-free loop the compiler can vectorize.

void cf3_slow(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        if (in[i] > 0.0) {                          // Always true in practice
            out[i] = in[i] * in[i] + in[i] * 0.5;
        } else {
            out[i] = 0.0;                            // Dead code for this data
        }
    }
}

void cf3_fast(double *out, double *in, int n) {
    // Verify runtime guarantee once: all values are positive
    int all_pos = 1;
    for (int i = 0; i < n; i++) {
        if (in[i] <= 0.0) { all_pos = 0; break; }
    }
    if (all_pos) {
        // Branch-free: compiler can auto-vectorize
        for (int i = 0; i < n; i++)
            out[i] = in[i] * in[i] + in[i] * 0.5;
    } else {
        for (int i = 0; i < n; i++)
            out[i] = (in[i] > 0.0) ? in[i] * in[i] + in[i] * 0.5 : 0.0;
    }
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
