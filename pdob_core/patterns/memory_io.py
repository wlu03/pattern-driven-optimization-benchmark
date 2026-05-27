# Memory/IO patterns: MI-1 through MI-4.
from ._entry import PatternEntry


MI_PATTERNS = [
    PatternEntry(
        pattern_id="MI-1",
        category="Memory/IO",
        name="Allocation in Loop vs Sliding Window",
        compiler_difficulty="High",
        description="malloc / free for a window-sized buffer on every iteration of a moving-average loop. "
                    "Sliding window: maintain a running sum, add the entering element and subtract "
                    "the leaving one — no allocation needed.",
        slow_code="""
#include <stdlib.h>
double mi1_slow(double *input, int n, int window) {
    double total = 0.0;
    for (int i = 0; i <= n - window; i++) {
        double *buf = malloc(window * sizeof(double));
        for (int j = 0; j < window; j++) buf[j] = input[i + j];
        double sum = 0.0;
        for (int j = 0; j < window; j++) sum += buf[j];
        total += sum / window;
        free(buf);
    }
    return total;
}""",
        fast_code="""
double mi1_fast(double *input, int n, int window) {
    double total = 0.0;
    double sum = 0.0;
    for (int j = 0; j < window; j++) sum += input[j];
    total += sum / window;
    for (int i = 1; i <= n - window; i++) {
        sum += input[i + window - 1] - input[i - 1];
        total += sum / window;
    }
    return total;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 500000;
    int window = 32;
    double *input = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++)
        input[i] = ((double)rand() / RAND_MAX) * 100.0;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double result = optimized(input, n, window);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    /* compute expected with sliding window */
    double expected = 0.0;
    double sum = 0.0;
    for (int j = 0; j < window; j++) sum += input[j];
    expected += sum / window;
    for (int i = 1; i <= n - window; i++) {
        sum += input[i + window - 1] - input[i - 1];
        expected += sum / window;
    }
    int correct = _bench_close(result, expected, 1e-6, 1e-6);
    printf("result=%.10f time_ms=%.4f correct=%d\\n", result, ms, correct);
    free(input);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="MI-2",
        category="Memory/IO",
        name="Redundant Memory Zeroing",
        compiler_difficulty="Medium",
        description="memset(output, 0, ...) followed immediately by a loop that overwrites every element. "
                    "Remove the memset — the subsequent write makes it unnecessary.",
        slow_code="""
#include <string.h>
void mi2_slow(double *output, double *A, double *B, int n) {
    memset(output, 0, n * sizeof(double));
    for (int i = 0; i < n; i++) {
        output[i] = A[i] + B[i];
    }
}""",
        fast_code="""
void mi2_fast(double *output, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        output[i] = A[i] + B[i];
    }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *A   = malloc(n * sizeof(double));
    double *B   = malloc(n * sizeof(double));
    double *out = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) {
        A[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);
        B[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int r = 0; r < 5; r++) optimized(out, A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = ((end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6) / 5.0;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (!_bench_close(out[i], A[i] + B[i], 1e-9, 1e-9)) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(A); free(B); free(out);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="MI-3",
        category="Memory/IO",
        name="Heap Alloc in Hot Loop",
        compiler_difficulty="High",
        description="malloc(4 * sizeof(double)) for a tiny 4-element scratch buffer every iteration. "
                    "Use direct arithmetic or a stack array — zero allocation overhead.",
        slow_code="""
#include <stdlib.h>
double mi3_slow(double *data, int n) {
    double total = 0.0;
    for (int i = 0; i < n - 3; i++) {
        double *quad = malloc(4 * sizeof(double));
        quad[0] = data[i]; quad[1] = data[i+1];
        quad[2] = data[i+2]; quad[3] = data[i+3];
        total += (quad[0] + quad[1] + quad[2] + quad[3]) * 0.25;
        free(quad);
    }
    return total;
}""",
        fast_code="""
double mi3_fast(double *data, int n) {
    double total = 0.0;
    for (int i = 0; i < n - 3; i++) {
        total += (data[i] + data[i+1] + data[i+2] + data[i+3]) * 0.25;
    }
    return total;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 2000000;
    double *data = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++)
        data[i] = ((double)rand() / RAND_MAX) * 100.0;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double result = optimized(data, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    double expected = 0.0;
    for (int i = 0; i < n - 3; i++)
        expected += (data[i] + data[i+1] + data[i+2] + data[i+3]) * 0.25;
    int correct = _bench_close(result, expected, 1e-6, 1e-6);
    printf("result=%.10f time_ms=%.4f correct=%d\\n", result, ms, correct);
    free(data);
    return 0;
}"""
    ),

    PatternEntry(pattern_id="MI-4", category="Memory/IO", name="Column vs Row Major Access",
        compiler_difficulty="Medium",
        description="Column-major traversal in row-major C causes cache misses. "
                    "Swap loop order for sequential access.",
        slow_code="""
void mi4_slow(double *mat, int rows, int cols) {
    for (int j = 0; j < cols; j++)
        for (int i = 0; i < rows; i++)
            mat[i * cols + j] *= 2.0;
}""",
        fast_code="""
void mi4_fast(double *mat, int rows, int cols) {
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            mat[i * cols + j] *= 2.0;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int rows = 4000, cols = 4000;
    double *mat      = malloc(rows * cols * sizeof(double));
    double *expected = malloc(rows * cols * sizeof(double));
    srand(42);
    for (int i = 0; i < rows * cols; i++) mat[i] = expected[i] = (double)rand() / RAND_MAX;
    for (int i = 0; i < rows * cols; i++) expected[i] *= 2.0;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(mat, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < rows * cols; i++) {
        if (!_bench_close(mat[i], expected[i], 1e-9, 1e-9)) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", mat[0], ms, correct);
    free(mat); free(expected);
    return 0;
}"""
    ),
]
