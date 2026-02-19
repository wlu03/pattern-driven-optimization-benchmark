// Inefficiencies from coding habits, readability choices, defensive programming, and incremental development.
#include "../harness/bench_harness.h"

#define N 10000000

// HR-1: Redundant Temporary Variables
// Unnecessary intermediate variables that force extra
// memory writes and prevent register optimization.
void hr1_slow(double *out, double *A, double *B, double *C, int n) {
    for (int i = 0; i < n; i++) {
        double temp1 = A[i] + B[i];
        double temp2 = temp1 * C[i];
        double temp3 = temp2 + 1.0;
        double result = temp3;
        out[i] = result;
    }
}

void hr1_fast(double *out, double *A, double *B, double *C, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = (A[i] + B[i]) * C[i] + 1.0;
    }
}

// HR-2: Copy-Paste Duplication
// Developers copy-paste code blocks with minor variations,
// leading to duplicated computation that isn't trivially
// detectable by the compiler.
void hr2_slow(double *X, double *Y, int n,
              double *mean_x, double *mean_y,
              double *var_x, double *var_y) {
    // Compute mean of X
    double sum_x = 0.0;
    for (int i = 0; i < n; i++) sum_x += X[i];
    *mean_x = sum_x / n;

    // Compute mean of Y (copy-pasted from above)
    double sum_y = 0.0;
    for (int i = 0; i < n; i++) sum_y += Y[i];
    *mean_y = sum_y / n;

    // Compute variance of X
    double var_sum_x = 0.0;
    for (int i = 0; i < n; i++) {
        double diff = X[i] - *mean_x;
        var_sum_x += diff * diff;
    }
    *var_x = var_sum_x / n;

    // Compute variance of Y (copy-pasted)
    double var_sum_y = 0.0;
    for (int i = 0; i < n; i++) {
        double diff = Y[i] - *mean_y;
        var_sum_y += diff * diff;
    }
    *var_y = var_sum_y / n;
    // Total: 4 separate passes over the data
}

void hr2_fast(double *X, double *Y, int n,
              double *mean_x, double *mean_y,
              double *var_x, double *var_y) {
    // Single pass: compute both means
    double sx = 0.0, sy = 0.0;
    for (int i = 0; i < n; i++) {
        sx += X[i];
        sy += Y[i];
    }
    *mean_x = sx / n;
    *mean_y = sy / n;

    // Single pass: compute both variances
    double vx = 0.0, vy = 0.0;
    double mx = *mean_x, my = *mean_y;
    for (int i = 0; i < n; i++) {
        double dx = X[i] - mx;
        double dy = Y[i] - my;
        vx += dx * dx;
        vy += dy * dy;
    }
    *var_x = vx / n;
    *var_y = vy / n;
    // Total: 2 passes (could be 1 with Welford's)
}

// HR-3: Dead / Debug Code
// Logging, assertions, and diagnostic code left in production.
// Compiler can't remove because side effects are possible.
static volatile int debug_counter = 0;  // volatile prevents optimization

void hr3_slow(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        // Debug: track how many elements processed
        debug_counter++;

        // Debug: range validation (always true for normal data)
        if (in[i] != in[i]) {  // NaN check
            fprintf(stderr, "Warning: NaN at index %d\n", i);
        }

        out[i] = in[i] * 2.0 + 1.0;

        // Debug: verify output range
        if (out[i] < -1e15 || out[i] > 1e15) {
            fprintf(stderr, "Warning: output overflow at %d\n", i);
        }
    }
}

void hr3_fast(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * 2.0 + 1.0;
    }
}

// HR-4: Overly Defensive Null/Error Checks
// Checking for conditions that are impossible given the context,
// inside hot inner loops.
double hr4_slow(double *arr, int n) {
    if (arr == NULL) return 0.0;  // once
    if (n <= 0) return 0.0;       // once

    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;     // Redundant: already checked
        if (n <= 0) break;              // Redundant: loop wouldn't run
        if (i < 0 || i >= n) continue;  // Impossible: loop guarantees
        double val = arr[i];
        if (val != val) continue;       // NaN check every iteration
        sum += val;
    }
    return sum;
}

double hr4_fast(double *arr, int n) {
    if (arr == NULL || n <= 0) return 0.0;

    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum;
}

// HR-5: Repeated String/Format Operations
// Building output through repeated small format calls instead
// of batched operations. (Using integer arrays to simulate)

// Simulate: building a result array element-by-element with
// redundant boundary management vs. bulk operation
void hr5_slow(int *out, int *A, int *B, int n) {
    int pos = 0;
    for (int i = 0; i < n; i++) {
        // "Append" pattern: check capacity, compute, store, increment
        if (pos < n) {
            int val = A[i] + B[i];
            if (val >= 0) {  // Defensive: always true for our data
                out[pos] = val;
                pos = pos + 1;
            }
        }
    }
}

void hr5_fast(int *out, int *A, int *B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] + B[i];
    }
}

void run_human_style(void) {
    srand(42);
    double *A = malloc(N * sizeof(double));
    double *B = malloc(N * sizeof(double));
    double *C = malloc(N * sizeof(double));
    double *out_slow = malloc(N * sizeof(double));
    double *out_fast = malloc(N * sizeof(double));

    fill_random_double(A, N, -10.0, 10.0);
    fill_random_double(B, N, -10.0, 10.0);
    fill_random_double(C, N, 0.1, 5.0);

    // HR-1
    {
        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) hr1_slow(out_slow, A, B, C, N);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) hr1_fast(out_fast, A, B, C, N);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("HR-1", "Redundant Temporary Variables", ms_slow, ms_fast, ok);
        printf("[HR-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // HR-2
    {
        double mx_s, my_s, vx_s, vy_s;
        double mx_f, my_f, vx_f, vy_f;

        BenchTimer t;
        timer_start(&t);
        hr2_slow(A, B, N, &mx_s, &my_s, &vx_s, &vy_s);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        hr2_fast(A, B, N, &mx_f, &my_f, &vx_f, &vy_f);
        double ms_fast = timer_stop(&t);

        int ok = verify_double(mx_s, mx_f, 1e-9) && verify_double(my_s, my_f, 1e-9)
              && verify_double(vx_s, vx_f, 1e-9) && verify_double(vy_s, vy_f, 1e-9);
        record_result("HR-2", "Copy-Paste Duplication", ms_slow, ms_fast, ok);
        printf("[HR-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // HR-3
    {
        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 3; r++) hr3_slow(out_slow, A, N);
        double ms_slow = timer_stop(&t) / 3.0;

        timer_start(&t);
        for (int r = 0; r < 3; r++) hr3_fast(out_fast, A, N);
        double ms_fast = timer_stop(&t) / 3.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("HR-3", "Dead / Debug Code", ms_slow, ms_fast, ok);
        printf("[HR-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // HR-4
    {
        BenchTimer t;
        double r_slow, r_fast;

        timer_start(&t);
        for (int r = 0; r < 10; r++) r_slow = hr4_slow(A, N);
        double ms_slow = timer_stop(&t) / 10.0;

        timer_start(&t);
        for (int r = 0; r < 10; r++) r_fast = hr4_fast(A, N);
        double ms_fast = timer_stop(&t) / 10.0;

        int ok = verify_double(r_slow, r_fast, 1e-9);
        record_result("HR-4", "Overly Defensive Checks", ms_slow, ms_fast, ok);
        printf("[HR-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // HR-5
    {
        int *iA = malloc(N * sizeof(int));
        int *iB = malloc(N * sizeof(int));
        int *iout_slow = malloc(N * sizeof(int));
        int *iout_fast = malloc(N * sizeof(int));
        fill_random_int(iA, N, 0, 1000);
        fill_random_int(iB, N, 0, 1000);

        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) hr5_slow(iout_slow, iA, iB, N);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) hr5_fast(iout_fast, iA, iB, N);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_int(iout_slow, iout_fast, N);
        record_result("HR-5", "String Building Anti-patterns", ms_slow, ms_fast, ok);
        printf("[HR-5] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(iA); free(iB); free(iout_slow); free(iout_fast);
    }

    free(A); free(B); free(C); free(out_slow); free(out_fast);
}
