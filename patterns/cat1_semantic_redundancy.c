#include "../harness/bench_harness.h"
#include <math.h>
#define N 1000000

// SR-1: Loop-Invariant Function Call (Log Series)
// A 40-term log-series function is called with loop-invariant arguments
// on every iteration. The transcendental inner loop prevents the compiler
// from proving the result is loop-invariant. Hoist once before the loop.
static double log_series(double base) {
    double r = 0.0;
    for (int k = 1; k <= 40; k++) r += log(base * k + 1.0) / k;
    return r;
}
void sr1_slow(double *arr, int n, double base) {
    for (int i = 0; i < n; i++)
        arr[i] *= log_series(base);  /* same result every iteration */
}
void sr1_fast(double *arr, int n, double base) {
    double scale = log_series(base);  /* hoisted once */
    for (int i = 0; i < n; i++) arr[i] *= scale;
}

// SR-2: Loop-Invariant Term in Mixed Expression
// penalty(alpha, beta) has a sin/exp inner loop — compiler cannot hoist
// because transcendental functions block pure/const analysis.
// Optimization: separate accumulators, call penalty once, multiply by n.
static double penalty(double a, double b) {
    double r = 0.0;
    for (int k = 1; k <= 20; k++) r += sin(a * k) * exp(-b * k * 0.05);
    return r;
}
__attribute__((noinline))
double sr2_slow(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++)
        result += alpha * X[i] * X[i] + beta * Y[i] + penalty(alpha, beta);
    return result;
}
__attribute__((noinline))
double sr2_fast(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0.0, sumY = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY   += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (double)n * penalty(alpha, beta);
}

// SR-3: Redundant Aggregation Recomputation
// Recomputing an aggregate (mean) from scratch every iteration (O(n^2))
// instead of maintaining a running sum (O(n)).
void sr3_slow(double *data, double *running_avg, int n) {
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j <= i; j++) sum += data[j];
        running_avg[i] = sum / (i + 1);
    }
}
void sr3_fast(double *data, double *running_avg, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        running_avg[i] = sum / (i + 1);
    }
}

// SR-4: Invariant Function Call in Loop (Cross-TU boundary)
// In evaluate_llm.py this lives in a separate translation unit so the compiler
// cannot see inside it. Here it's defined inline for the bench binary.
__attribute__((noinline))
double expensive_lookup(int key) {
    double result = 0.0;
    for (int i = 0; i < 100; i++)
        result += sin((double)(key + i)) * cos((double)(key - i));
    return result;
}

void sr4_slow(double *arr, int n, int config_key) {
    for (int i = 0; i < n; i++) {
        double factor = expensive_lookup(config_key);  /* same every iteration */
        arr[i] *= factor;
    }
}
void sr4_fast(double *arr, int n, int config_key) {
    double factor = expensive_lookup(config_key);  /* hoisted */
    for (int i = 0; i < n; i++) arr[i] *= factor;
}

// SR-5: Repeated Division by Loop-Invariant Denominator
// compute_norm(w, m) is called every iteration. Without restrict qualifiers,
// out[] could alias w[], so the compiler must re-evaluate it each iteration.
// Optimization: call once, precompute reciprocal, use multiply.
static double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    return sqrt(s);
}
__attribute__((noinline))
void sr5_slow(double *out, double *data, int n, double *w, int m) {
    for (int i = 0; i < n; i++)
        out[i] = data[i] / compute_norm(w, m);  /* recomputed every iteration */
}
__attribute__((noinline))
void sr5_fast(double *out, double *data, int n, double *w, int m) {
    double inv = 1.0 / compute_norm(w, m);  /* hoist + reciprocal */
    for (int i = 0; i < n; i++) out[i] = data[i] * inv;
}


void run_semantic_redundancy(void) {
    srand(42);
    double *arr1s = malloc(N * sizeof(double));
    double *arr1f = malloc(N * sizeof(double));
    double *X = malloc(N * sizeof(double));
    double *Y = malloc(N * sizeof(double));
    double *data5 = malloc(N * sizeof(double));
    double *out5s = malloc(N * sizeof(double));
    double *out5f = malloc(N * sizeof(double));
    int m5 = 256;
    double *w5 = malloc(m5 * sizeof(double));

    fill_random_double(arr1s, N, 0.5, 1.5);
    memcpy(arr1f, arr1s, N * sizeof(double));
    fill_random_double(X, N, -5.0, 5.0);
    fill_random_double(Y, N, -5.0, 5.0);
    fill_random_double(data5, N, -5.0, 5.0);
    fill_random_double(w5, m5, 0.0, 1.0);

    // SR-1
    {
        double base = 1.5;
        double *s1 = malloc(N * sizeof(double));
        double *f1 = malloc(N * sizeof(double));
        memcpy(s1, arr1s, N * sizeof(double));
        memcpy(f1, arr1s, N * sizeof(double));

        BenchTimer t;
        timer_start(&t);
        sr1_slow(s1, N, base);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        sr1_fast(f1, N, base);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(s1, f1, N, 1e-6);
        record_result("SR-1", "Loop-Invariant Function Call (Log Series)", ms_slow, ms_fast, ok);
        printf("[SR-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
        free(s1); free(f1);
    }

    // SR-2
    {
        double alpha = 2.5, beta = 1.5;
        BenchTimer t;
        double r_slow, r_fast;

        timer_start(&t);
        r_slow = sr2_slow(X, Y, N, alpha, beta);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        r_fast = sr2_fast(X, Y, N, alpha, beta);
        double ms_fast = timer_stop(&t);

        int ok = verify_double(r_slow, r_fast, 1e-4);
        record_result("SR-2", "Loop-Invariant Term in Mixed Expression", ms_slow, ms_fast, ok);
        printf("[SR-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // SR-3
    {
        int n3 = 20000;  // O(n^2) — keep smaller
        double *data3 = malloc(n3 * sizeof(double));
        fill_random_double(data3, n3, 0.0, 100.0);
        double *avg_slow = malloc(n3 * sizeof(double));
        double *avg_fast = malloc(n3 * sizeof(double));

        BenchTimer t;
        timer_start(&t);
        sr3_slow(data3, avg_slow, n3);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        sr3_fast(data3, avg_fast, n3);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(avg_slow, avg_fast, n3, 1e-9);
        record_result("SR-3", "Redundant Aggregation Recomputation", ms_slow, ms_fast, ok);
        printf("[SR-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
        free(data3); free(avg_slow); free(avg_fast);
    }

    // SR-4
    {
        int n4 = 1000000;
        double *arr_slow = malloc(n4 * sizeof(double));
        double *arr_fast = malloc(n4 * sizeof(double));
        fill_random_double(arr_slow, n4, 1.0, 10.0);
        memcpy(arr_fast, arr_slow, n4 * sizeof(double));

        BenchTimer t;
        timer_start(&t);
        sr4_slow(arr_slow, n4, 42);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        sr4_fast(arr_fast, n4, 42);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(arr_slow, arr_fast, n4, 1e-12);
        record_result("SR-4", "Invariant Function Call in Loop", ms_slow, ms_fast, ok);
        printf("[SR-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
        free(arr_slow); free(arr_fast);
    }

    // SR-5
    {
        BenchTimer t;
        timer_start(&t);
        sr5_slow(out5s, data5, N, w5, m5);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        sr5_fast(out5f, data5, N, w5, m5);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(out5s, out5f, N, 1e-9);
        record_result("SR-5", "Repeated Division by Loop-Invariant Denominator", ms_slow, ms_fast, ok);
        printf("[SR-5] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    free(arr1s); free(arr1f);
    free(X); free(Y);
    free(data5); free(out5s); free(out5f); free(w5);
}
