#include "../harness/bench_harness.h"
#define N 10000000

// SR-1: Loop-Invariant Semantic Computation
// The expression `B[i] * delta` has `delta` invariant across
// iterations, but the accumulation structure hides this from
// the compiler due to FP associativity concerns.
double sr1_slow(double *A, double *B, int n, double delta) {
    double t = 0.0;
    for (int i = 0; i < n; i++) {
        t += A[i] + B[i] * delta;   // delta * B[i] recomputed per iter
    }
    return t;
}

double sr1_fast(double *A, double *B, int n, double delta) {
    double sumA = 0.0, sumB = 0.0;
    for (int i = 0; i < n; i++) {
        sumA += A[i];
        sumB += B[i];
    }
    return sumA + sumB * delta;  // Single multiply at the end
}

// SR-2: Recomputable Expression Decomposition
// A complex expression inside a loop can be algebraically
// decomposed into independent accumulators.
double sr2_slow(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] * X[i] + beta * Y[i] + alpha * beta;
    }
    return result;
}

double sr2_fast(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0.0, sumY = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (double)n * alpha * beta;
}

// SR-3: Redundant Aggregation Recomputation
// Recomputing an aggregate (mean, sum) from scratch every
// iteration instead of maintaining a running value.
void sr3_slow(double *data, double *running_avg, int n) {
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j <= i; j++) {
            sum += data[j];
        }
        running_avg[i] = sum / (i + 1);  // O(n^2) total
    }
}

void sr3_fast(double *data, double *running_avg, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        running_avg[i] = sum / (i + 1);  // O(n) total
    }
}

// SR-4: Invariant Function Call in Loop
// Calling a pure function with loop-invariant arguments inside
// a loop. Compiler can't hoist if function has side effects
// or is in a different translation unit.

// Simulating an "expensive" pure function
double expensive_config_lookup(int key) {
    // Simulate work: hash + lookup
    double result = 0.0;
    for (int i = 0; i < 100; i++) {
        result += sin((double)(key + i)) * cos((double)(key - i));
    }
    return result;
}

void sr4_slow(double *arr, int n, int config_key) {
    for (int i = 0; i < n; i++) {
        double factor = expensive_config_lookup(config_key);  // same every iteration
        arr[i] *= factor;
    }
}

void sr4_fast(double *arr, int n, int config_key) {
    double factor = expensive_config_lookup(config_key);  // hoisted
    for (int i = 0; i < n; i++) {
        arr[i] *= factor;
    }
}

// SR-5: Algebraic Strength Reduction (Semantic Level)
// Using expensive operations (pow, sqrt, division) when cheaper
// algebraic equivalents exist. Beyond compiler strength reduction
// because it requires semantic understanding.
void sr5_slow(double *distances, double *X, double *Y, int n,
              double cx, double cy) {
    for (int i = 0; i < n; i++) {
        // Full Euclidean distance - expensive sqrt
        distances[i] = sqrt((X[i] - cx) * (X[i] - cx) +
                           (Y[i] - cy) * (Y[i] - cy));
    }
}

void sr5_fast_sqd(double *distances, double *X, double *Y, int n,
                  double cx, double cy) {
    // If we only need to compare/sort distances, squared distance suffices
    for (int i = 0; i < n; i++) {
        double dx = X[i] - cx, dy = Y[i] - cy;
        distances[i] = dx * dx + dy * dy;  // Skip sqrt
    }
}


void run_semantic_redundancy(void) {
    srand(42);
    double *A = malloc(N * sizeof(double));
    double *B = malloc(N * sizeof(double));
    double *X = malloc(N * sizeof(double));
    double *Y = malloc(N * sizeof(double));
    double *out_slow = malloc(N * sizeof(double));
    double *out_fast = malloc(N * sizeof(double));

    fill_random_double(A, N, -10.0, 10.0);
    fill_random_double(B, N, -10.0, 10.0);
    fill_random_double(X, N, -100.0, 100.0);
    fill_random_double(Y, N, -100.0, 100.0);

    // SR-1
    {
        double delta = 3.14159;
        BenchTimer t;
        double r_slow, r_fast;

        timer_start(&t);
        for (int rep = 0; rep < 5; rep++) r_slow = sr1_slow(A, B, N, delta);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int rep = 0; rep < 5; rep++) r_fast = sr1_fast(A, B, N, delta);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_double(r_slow, r_fast, 1e-6);
        record_result("SR-1", "Loop-Invariant Semantic Computation", ms_slow, ms_fast, ok);
        printf("[SR-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // SR-2
    {
        double alpha = 2.5, beta = 1.7;
        BenchTimer t;
        double r_slow, r_fast;

        timer_start(&t);
        for (int rep = 0; rep < 5; rep++) r_slow = sr2_slow(X, Y, N, alpha, beta);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int rep = 0; rep < 5; rep++) r_fast = sr2_fast(X, Y, N, alpha, beta);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_double(r_slow, r_fast, 1e-6);
        record_result("SR-2", "Recomputable Expression Decomposition", ms_slow, ms_fast, ok);
        printf("[SR-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // SR-3
    {
        int n3 = 50000;  // O(n^2) so keep smaller
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
        sr5_slow(out_slow, X, Y, N, 0.0, 0.0);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        sr5_fast_sqd(out_fast, X, Y, N, 0.0, 0.0);
        double ms_fast = timer_stop(&t);

        // Verify: out_slow[i]^2 should equal out_fast[i]
        int ok = 1;
        for (int i = 0; i < 1000; i++) {
            if (!verify_double(out_slow[i] * out_slow[i], out_fast[i], 1e-9)) {
                ok = 0; break;
            }
        }
        record_result("SR-5", "Algebraic Strength Reduction", ms_slow, ms_fast, ok);
        printf("[SR-5] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    free(A); free(B); free(X); free(Y); free(out_slow); free(out_fast);
}
