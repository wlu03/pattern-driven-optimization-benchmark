// Performance degradation that depends on runtime data characteristics.
// Static analysis cannot determine data distributions at compile time.
#include "../harness/bench_harness.h"
#define N 10000000

// IS-1: Sparse Data Redundancy (Zero-Skip)
// When data is mostly zeros, computation and memory writes
// are wasted. Compiler can't add runtime sparsity checks.
void is1_slow(double *weights, double *delta, double *layer,
              int nj, int nk) {
    for (int k = 0; k < nk; k++) {
        for (int j = 0; j < nj; j++) {
            double new_dw = delta[j] * layer[k];
            weights[k * nj + j] += new_dw;  // Always writes, even if 0
        }
    }
}

void is1_fast(double *weights, double *delta, double *layer,
              int nj, int nk) {
    for (int k = 0; k < nk; k++) {
        if (layer[k] == 0.0) continue;  // Skip entire row if zero
        for (int j = 0; j < nj; j++) {
            if (delta[j] == 0.0) continue;  // Skip zero delta
            double new_dw = delta[j] * layer[k];
            weights[k * nj + j] += new_dw;
        }
    }
}

// IS-2: Data Distribution Skew
// When most values fall in a narrow range, a cheap fast-path
// can handle the common case while a slow path handles outliers.
// Think: gradient clipping where 99% of gradients are small.
void is2_slow(double *output, double *input, int n,
              double threshold) {
    for (int i = 0; i < n; i++) {
        // Always compute full expensive clipping + normalization
        double val = input[i];
        double sign = (val >= 0) ? 1.0 : -1.0;
        double abs_val = fabs(val);
        if (abs_val > threshold) {
            output[i] = sign * (threshold + log(1.0 + abs_val - threshold));
        } else {
            output[i] = val;  // Common case: just copy
        }
    }
}

void is2_fast(double *output, double *input, int n,
              double threshold) {
    // First pass: cheap comparison to identify the common case
    for (int i = 0; i < n; i++) {
        double val = input[i];
        if (fabs(val) <= threshold) {
            output[i] = val;  // Fast path: 99% of data
        } else {
            // Slow path: rare outliers
            double sign = (val >= 0) ? 1.0 : -1.0;
            double abs_val = fabs(val);
            output[i] = sign * (threshold + log(1.0 + abs_val - threshold));
        }
    }
}

// IS-3: Early Termination Opportunities
// When searching or validating, the loop continues even after
// the answer is determined. Compilers can't add early exits
// without semantic understanding.
// Check if all elements satisfy a condition
int is3_slow(double *arr, int n, double threshold) {
    int count_violations = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] > threshold) {
            count_violations++;  // Counts ALL violations
        }
    }
    return count_violations == 0;  // Just needed yes/no
}

int is3_fast(double *arr, int n, double threshold) {
    for (int i = 0; i < n; i++) {
        if (arr[i] > threshold) {
            return 0;  // Early exit on first violation
        }
    }
    return 1;
}

// IS-4: Sorted/Presorted Input Exploitation
// When input is already sorted (or nearly sorted), using a
// generic O(n log n) sort is wasteful. An insertion sort or
// just a verification pass is sufficient.
static int cmp_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}

void is4_slow(int *arr, int n) {
    // Always use generic sort regardless of input order
    qsort(arr, n, sizeof(int), cmp_int);
}

void is4_fast(int *arr, int n) {
    // Check if already sorted (or nearly sorted) first
    int sorted = 1;
    for (int i = 1; i < n; i++) {
        if (arr[i] < arr[i-1]) { sorted = 0; break; }
    }
    if (sorted) return;  // O(n) check saves O(n log n) sort

    // Fallback to sort
    qsort(arr, n, sizeof(int), cmp_int);
}


void run_input_sensitive(void) {
    srand(42);
    // IS-1: Sparse neural network weights
    {
        int nj = 3000, nk = 3000;
        int total = nj * nk;
        double *weights_slow = calloc(total, sizeof(double));
        double *weights_fast = calloc(total, sizeof(double));
        double *delta = malloc(nj * sizeof(double));
        double *layer = malloc(nk * sizeof(double));

        // 90% sparse
        fill_sparse_double(delta, nj, 0.9);
        fill_sparse_double(layer, nk, 0.9);

        BenchTimer t;
        timer_start(&t);
        is1_slow(weights_slow, delta, layer, nj, nk);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        is1_fast(weights_fast, delta, layer, nj, nk);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(weights_slow, weights_fast, total, 1e-12);
        record_result("IS-1", "Sparse Data Redundancy (zero-skip)", ms_slow, ms_fast, ok);
        printf("[IS-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(weights_slow); free(weights_fast); free(delta); free(layer);
    }

    // IS-2: Skewed distribution (99% values within threshold)
    {
        double *input = malloc(N * sizeof(double));
        double *out_slow = malloc(N * sizeof(double));
        double *out_fast = malloc(N * sizeof(double));

        // Generate skewed: 99% in [-1,1], 1% outliers
        for (int i = 0; i < N; i++) {
            if (rand() % 100 == 0)
                input[i] = 50.0 * ((double)rand()/RAND_MAX - 0.5);
            else
                input[i] = 2.0 * ((double)rand()/RAND_MAX - 0.5);
        }
        double threshold = 1.0;

        BenchTimer t;
        timer_start(&t);
        is2_slow(out_slow, input, N, threshold);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        is2_fast(out_fast, input, N, threshold);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("IS-2", "Data Distribution Skew", ms_slow, ms_fast, ok);
        printf("[IS-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(input); free(out_slow); free(out_fast);
    }

    // IS-3: Early termination (violation near start)
    {
        double *arr = malloc(N * sizeof(double));
        fill_random_double(arr, N, 0.0, 1.0);
        arr[5] = 999.0;  // Violation very early

        BenchTimer t;
        timer_start(&t);
        for (int rep = 0; rep < 20; rep++) is3_slow(arr, N, 100.0);
        double ms_slow = timer_stop(&t) / 20.0;

        timer_start(&t);
        for (int rep = 0; rep < 20; rep++) is3_fast(arr, N, 100.0);
        double ms_fast = timer_stop(&t) / 20.0;

        int ok = (is3_slow(arr, N, 100.0) == is3_fast(arr, N, 100.0));
        record_result("IS-3", "Early Termination Opportunities", ms_slow, ms_fast, ok);
        printf("[IS-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(arr);
    }

    // IS-4: Already-sorted input
    {
        int n4 = 5000000;
        int *arr_slow = malloc(n4 * sizeof(int));
        int *arr_fast = malloc(n4 * sizeof(int));
        for (int i = 0; i < n4; i++) arr_slow[i] = i;  // Already sorted
        memcpy(arr_fast, arr_slow, n4 * sizeof(int));

        BenchTimer t;
        timer_start(&t);
        is4_slow(arr_slow, n4);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        is4_fast(arr_fast, n4);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_int(arr_slow, arr_fast, n4);
        record_result("IS-4", "Sorted Input Exploitation", ms_slow, ms_fast, ok);
        printf("[IS-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(arr_slow); free(arr_fast);
    }
}
