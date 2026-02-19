// Wasteful memory operations, allocation patterns, and I/O practices that hurt performance.
#include "../harness/bench_harness.h"
#define N 5000000

// MI-1: Unnecessary Memory Allocation in Loop
// Creating and destroying objects/buffers inside a tight loop
// instead of reusing them.
double mi1_slow(double *input, int n, int window) {
    double total = 0.0;
    for (int i = 0; i <= n - window; i++) {
        double *buf = malloc(window * sizeof(double));  // Alloc each iter
        for (int j = 0; j < window; j++) buf[j] = input[i + j];
        double sum = 0.0;
        for (int j = 0; j < window; j++) sum += buf[j];
        total += sum / window;
        free(buf);
    }
    return total;
}

double mi1_fast(double *input, int n, int window) {
    double total = 0.0;
    // Sliding window: no allocation at all
    double sum = 0.0;
    for (int j = 0; j < window; j++) sum += input[j];
    total += sum / window;
    for (int i = 1; i <= n - window; i++) {
        sum += input[i + window - 1] - input[i - 1];
        total += sum / window;
    }
    return total;
}

// MI-2: Redundant Memory Zeroing
// Clearing memory that will be immediately overwritten.
// Common in scientific codes that zero-initialize arrays
// before filling them.
void mi2_slow(double *output, double *A, double *B, int n) {
    // Zero the output array first
    memset(output, 0, n * sizeof(double));
    // Then overwrite every element anyway
    for (int i = 0; i < n; i++) {
        output[i] = A[i] + B[i];
    }
}

void mi2_fast(double *output, double *A, double *B, int n) {
    // Direct write - no zeroing needed
    for (int i = 0; i < n; i++) {
        output[i] = A[i] + B[i];
    }
}

// MI-3: Excessive Dynamic Allocation (malloc in hot loop)
// Using heap allocation for small, short-lived data that
// could live on the stack or be pre-allocated.
double mi3_slow(double *data, int n) {
    double total = 0.0;
    for (int i = 0; i < n - 3; i++) {
        // Allocate a small 4-element array on heap each time
        double *quad = malloc(4 * sizeof(double));
        quad[0] = data[i]; quad[1] = data[i+1];
        quad[2] = data[i+2]; quad[3] = data[i+3];
        total += (quad[0] + quad[1] + quad[2] + quad[3]) * 0.25;
        free(quad);
    }
    return total;
}

double mi3_fast(double *data, int n) {
    double total = 0.0;
    for (int i = 0; i < n - 3; i++) {
        // Stack array or direct computation
        total += (data[i] + data[i+1] + data[i+2] + data[i+3]) * 0.25;
    }
    return total;
}

// MI-4: Column-Major vs Row-Major Access
// Accessing a 2D array in the wrong order relative to memory
// layout causes cache misses. C uses row-major.
void mi4_slow(double *matrix, int rows, int cols) {
    // Column-major traversal in a row-major language → cache misses
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            matrix[i * cols + j] *= 2.0;  // Stride = cols * 8 bytes
        }
    }
}

void mi4_fast(double *matrix, int rows, int cols) {
    // Row-major traversal → sequential memory access
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i * cols + j] *= 2.0;  // Stride = 8 bytes
        }
    }
}


void run_memory_io(void) {
    srand(42);

    // MI-1: Alloc in loop vs sliding window
    {
        int n1 = 500000;
        int window = 32;
        double *input = malloc(n1 * sizeof(double));
        fill_random_double(input, n1, 0.0, 100.0);

        BenchTimer t;
        double r_slow, r_fast;

        timer_start(&t);
        r_slow = mi1_slow(input, n1, window);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        r_fast = mi1_fast(input, n1, window);
        double ms_fast = timer_stop(&t);

        int ok = verify_double(r_slow, r_fast, 1e-6);
        record_result("MI-1", "Allocation in Loop vs Sliding Window", ms_slow, ms_fast, ok);
        printf("[MI-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(input);
    }

    // MI-2: Redundant zeroing
    {
        double *A = malloc(N * sizeof(double));
        double *B = malloc(N * sizeof(double));
        double *out_slow = malloc(N * sizeof(double));
        double *out_fast = malloc(N * sizeof(double));
        fill_random_double(A, N, -10.0, 10.0);
        fill_random_double(B, N, -10.0, 10.0);

        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) mi2_slow(out_slow, A, B, N);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) mi2_fast(out_fast, A, B, N);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("MI-2", "Redundant Memory Zeroing", ms_slow, ms_fast, ok);
        printf("[MI-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(A); free(B); free(out_slow); free(out_fast);
    }

    // MI-3: Heap vs stack allocation
    {
        int n3 = 2000000;
        double *data = malloc(n3 * sizeof(double));
        fill_random_double(data, n3, 0.0, 100.0);

        BenchTimer t;
        double r_slow, r_fast;

        timer_start(&t);
        r_slow = mi3_slow(data, n3);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        r_fast = mi3_fast(data, n3);
        double ms_fast = timer_stop(&t);

        int ok = verify_double(r_slow, r_fast, 1e-6);
        record_result("MI-3", "Heap Alloc in Hot Loop", ms_slow, ms_fast, ok);
        printf("[MI-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(data);
    }

    // MI-4: Column vs row major access
    {
        int rows = 4000, cols = 4000;
        double *mat_slow = malloc(rows * cols * sizeof(double));
        double *mat_fast = malloc(rows * cols * sizeof(double));
        fill_random_double(mat_slow, rows * cols, 1.0, 10.0);
        memcpy(mat_fast, mat_slow, rows * cols * sizeof(double));

        BenchTimer t;
        timer_start(&t);
        mi4_slow(mat_slow, rows, cols);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        mi4_fast(mat_fast, rows, cols);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(mat_slow, mat_fast, rows * cols, 1e-12);
        record_result("MI-4", "Column vs Row Major Access", ms_slow, ms_fast, ok);
        printf("[MI-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(mat_slow); free(mat_fast);
    }
}
