// Conservative branching, overly defensive structures, and loop constructs that waste cycles.

#include "../harness/bench_harness.h"

#define N 10000000

// CF-1: Loop-Invariant Conditional (Hoistable Branch)
// A branch on a loop-invariant value is checked every iteration.
// Compiler may not hoist due to potential side effects or aliasing.
void cf1_slow(double *out, double *A, double *B, int n, int mode) {
    for (int i = 0; i < n; i++) {
        if (mode == 1) {
            out[i] = A[i] + B[i];
        } else if (mode == 2) {
            out[i] = A[i] * B[i];
        } else {
            out[i] = A[i] - B[i];
        }
    }
}

void cf1_fast(double *out, double *A, double *B, int n, int mode) {
    if (mode == 1) {
        for (int i = 0; i < n; i++) out[i] = A[i] + B[i];
    } else if (mode == 2) {
        for (int i = 0; i < n; i++) out[i] = A[i] * B[i];
    } else {
        for (int i = 0; i < n; i++) out[i] = A[i] - B[i];
    }
}

// CF-2: Redundant Bounds Checking
// Defensive bounds checks inside hot inner loops that are
// guaranteed by the outer loop structure.
void cf2_slow(double *matrix, int rows, int cols, double *row_sums) {
    for (int i = 0; i < rows; i++) {
        row_sums[i] = 0.0;
        for (int j = 0; j < cols; j++) {
            // Redundant: i and j are always in bounds due to loop limits
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                row_sums[i] += matrix[i * cols + j];
            }
        }
    }
}

void cf2_fast(double *matrix, int rows, int cols, double *row_sums) {
    for (int i = 0; i < rows; i++) {
        row_sums[i] = 0.0;
        for (int j = 0; j < cols; j++) {
            row_sums[i] += matrix[i * cols + j];  // Bounds guaranteed
        }
    }
}

// CF-3: Unnecessary Loop Nesting (Collapsible Loops)
// Nested loops over a logically flat iteration space.
// Flattening reduces loop overhead and enables vectorization.
void cf3_slow(double *matrix, int rows, int cols, double scalar) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i * cols + j] *= scalar;
        }
    }
}

void cf3_fast(double *matrix, int rows, int cols, double scalar) {
    int total = rows * cols;
    for (int idx = 0; idx < total; idx++) {
        matrix[idx] *= scalar;
    }
}

// CF-4: Premature Generalization (Overly Generic Dispatch)
// Using a generic/polymorphic dispatch mechanism (switch,
// function pointers) when the type/case is known or constant.
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
    for (int i = 0; i < n; i++) {
        out[i] = apply_op(op, A[i], B[i]);  // Switch dispatch every iter
    }
}

void cf4_fast(double *out, double *A, double *B, int n, OpType op) {
    // Resolve dispatch once, then tight loop
    switch(op) {
        case OP_ADD:
            for (int i = 0; i < n; i++) out[i] = A[i] + B[i];
            break;
        case OP_MUL:
            for (int i = 0; i < n; i++) out[i] = A[i] * B[i];
            break;
        case OP_SUB:
            for (int i = 0; i < n; i++) out[i] = A[i] - B[i];
            break;
    }
}


void run_control_flow(void) {

    srand(42);
    double *A = malloc(N * sizeof(double));
    double *B = malloc(N * sizeof(double));
    double *out_slow = malloc(N * sizeof(double));
    double *out_fast = malloc(N * sizeof(double));

    fill_random_double(A, N, -10.0, 10.0);
    fill_random_double(B, N, -10.0, 10.0);

    // CF-1
    {
        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) cf1_slow(out_slow, A, B, N, 2);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) cf1_fast(out_fast, A, B, N, 2);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("CF-1", "Loop-Invariant Conditional", ms_slow, ms_fast, ok);
        printf("[CF-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // CF-2
    {
        int rows = 3000, cols = 3000;
        double *mat = malloc(rows * cols * sizeof(double));
        double *sums_slow = malloc(rows * sizeof(double));
        double *sums_fast = malloc(rows * sizeof(double));
        fill_random_double(mat, rows * cols, -5.0, 5.0);

        BenchTimer t;
        timer_start(&t);
        cf2_slow(mat, rows, cols, sums_slow);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        cf2_fast(mat, rows, cols, sums_fast);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(sums_slow, sums_fast, rows, 1e-9);
        record_result("CF-2", "Redundant Bounds Checking", ms_slow, ms_fast, ok);
        printf("[CF-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(mat); free(sums_slow); free(sums_fast);
    }

    // CF-3
    {
        int rows = 3000, cols = 3000;
        double *mat_slow = malloc(rows * cols * sizeof(double));
        double *mat_fast = malloc(rows * cols * sizeof(double));
        fill_random_double(mat_slow, rows * cols, 1.0, 10.0);
        memcpy(mat_fast, mat_slow, rows * cols * sizeof(double));

        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) cf3_slow(mat_slow, rows, cols, 1.00001);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) cf3_fast(mat_fast, rows, cols, 1.00001);
        double ms_fast = timer_stop(&t) / 5.0;

        // Reset and run once each for correctness check
        fill_random_double(mat_slow, rows * cols, 1.0, 10.0);
        memcpy(mat_fast, mat_slow, rows * cols * sizeof(double));
        cf3_slow(mat_slow, rows, cols, 2.5);
        cf3_fast(mat_fast, rows, cols, 2.5);
        int ok = verify_array_double(mat_slow, mat_fast, rows * cols, 1e-12);

        record_result("CF-3", "Unnecessary Loop Nesting", ms_slow, ms_fast, ok);
        printf("[CF-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(mat_slow); free(mat_fast);
    }

    // CF-4
    {
        BenchTimer t;
        timer_start(&t);
        for (int r = 0; r < 5; r++) cf4_slow(out_slow, A, B, N, OP_MUL);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) cf4_fast(out_fast, A, B, N, OP_MUL);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_array_double(out_slow, out_fast, N, 1e-12);
        record_result("CF-4", "Premature Generalization", ms_slow, ms_fast, ok);
        printf("[CF-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    free(A); free(B); free(out_slow); free(out_fast);
}
