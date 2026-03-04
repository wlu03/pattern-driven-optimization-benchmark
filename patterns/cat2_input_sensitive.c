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

// IS-4: Adaptive Algorithm Selection (Nearly-Sorted Detection)
// When input is nearly sorted (e.g. 99% elements already in order with a
// handful of local swaps), qsort still performs O(n log n) comparisons
// because it cannot inspect the data before choosing an algorithm.
// The compiler cannot substitute insertion sort — it doesn't know the
// data distribution until runtime. The fast version samples a fixed set
// of random index pairs to estimate the inversion rate. If the rate is
// below a threshold it falls through to insertion sort, which degrades
// to O(n) for nearly-ordered input. For genuinely random input both
// versions use qsort so performance is identical.
static int cmp_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}

void is4_slow(int *arr, int n) {
    // Always delegates to generic O(n log n) sort
    qsort(arr, n, sizeof(int), cmp_int);
}

void is4_fast(int *arr, int n) {
    // Sample SAMPLE_K random adjacent-ish pairs to estimate inversion rate.
    // This is O(1) and tells us whether insertion sort will be efficient.
    #define SAMPLE_K 64
    #define NEARLY_SORTED_THRESH 4   // ≤4 inversions in 64 samples ≈ ≤6% rate
    int inv = 0;
    unsigned seed = 12345u;
    for (int s = 0; s < SAMPLE_K; s++) {
        seed = seed * 1664525u + 1013904223u;  // LCG
        int i = (int)((seed >> 1) % (unsigned)(n - 1));
        if (arr[i] > arr[i + 1]) inv++;
    }
    if (inv <= NEARLY_SORTED_THRESH) {
        // Insertion sort: O(n + k*n) where k = actual inversion density.
        // For nearly-sorted input this is effectively O(n).
        for (int i = 1; i < n; i++) {
            int key = arr[i], j = i - 1;
            while (j >= 0 && arr[j] > key) {
                arr[j + 1] = arr[j];
                j--;
            }
            arr[j + 1] = key;
        }
    } else {
        qsort(arr, n, sizeof(int), cmp_int);
    }
    #undef SAMPLE_K
    #undef NEARLY_SORTED_THRESH
}


// IS-5: Runtime Alias Check for Fast-Path Vectorization
// When output and input buffers might alias, the compiler must generate
// conservative aliasing-safe code (runtime overlap checks or scalar
// fallback), blocking clean SIMD. The compiler cannot prove at compile
// time whether separately-allocated buffers overlap — that's determined
// by runtime pointer values. In practice, callers always pass disjoint
// malloc'd arrays. The fast version checks this once at runtime and
// dispatches to a __restrict__-qualified kernel, letting the compiler
// emit unguarded vectorized code with no alias guards.

// Separate noinline kernel so restrict applies even in single-TU builds
static void __attribute__((noinline))
is5_restrict_kernel(double * __restrict__ out,
                    const double * __restrict__ A,
                    const double * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
    }
}

// noinline forces the compiler to compile conservatively (no call-site
// alias info): it can't prove A, B, out don't overlap from the definition.
__attribute__((noinline))
void is5_slow(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
    }
}

void is5_fast(double *out, double *A, double *B, int n) {
    // Runtime check: are all buffer pairs non-overlapping? (almost always true)
    int no_alias = (out + n <= A || A + n <= out) &&
                   (out + n <= B || B + n <= out);
    if (no_alias) {
        is5_restrict_kernel(out, A, B, n);  // Fast: restrict enables clean SIMD
    } else {
        // Correct fallback for aliasing callers (rare)
        for (int i = 0; i < n; i++) {
            out[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
        }
    }
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

    // IS-4: Nearly-sorted input (1% random swaps)
    {
        int n4 = 5000000;
        int *arr_slow = malloc(n4 * sizeof(int));
        int *arr_fast = malloc(n4 * sizeof(int));
        // Start sorted, then introduce ~1% local swaps so it's "nearly sorted"
        for (int i = 0; i < n4; i++) arr_slow[i] = i;
        srand(99);
        int swaps = n4 / 100;
        for (int s = 0; s < swaps; s++) {
            int i = rand() % (n4 - 1);
            int tmp = arr_slow[i]; arr_slow[i] = arr_slow[i+1]; arr_slow[i+1] = tmp;
        }
        memcpy(arr_fast, arr_slow, n4 * sizeof(int));

        BenchTimer t;
        timer_start(&t);
        is4_slow(arr_slow, n4);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        is4_fast(arr_fast, n4);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_int(arr_slow, arr_fast, n4);
        record_result("IS-4", "Adaptive Sort (nearly-sorted detection)", ms_slow, ms_fast, ok);
        printf("[IS-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(arr_slow); free(arr_fast);
    }

    // IS-5: Runtime alias check — separately malloc'd buffers never overlap
    {
        double *A   = malloc(N * sizeof(double));
        double *B   = malloc(N * sizeof(double));
        double *out_slow = malloc(N * sizeof(double));
        double *out_fast = malloc(N * sizeof(double));
        fill_random_double(A, N, 0.5, 5.0);
        fill_random_double(B, N, 0.5, 5.0);

        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) is5_slow(out_slow, A, B, N);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) is5_fast(out_fast, A, B, N);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("IS-5", "Runtime Alias Check (restrict fast path)", ms_slow, ms_fast, ok);
        printf("[IS-5] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(A); free(B); free(out_slow); free(out_fast);
    }
}
