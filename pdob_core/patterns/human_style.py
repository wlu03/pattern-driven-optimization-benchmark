# Human-Style Antipatterns: HR-2, HR-3, HR-4.
from ._entry import PatternEntry


HR_PATTERNS = [
    PatternEntry(
        pattern_id="HR-2",
        category="Human-Style Antipatterns",
        name="Copy-Paste Duplication",
        compiler_difficulty="Medium",
        description="Four separate passes over data (mean X, mean Y, var X, var Y) from "
                    "copy-pasted code blocks. Merge into two passes: one for both means, "
                    "one for both variances.",
        slow_code="""
void hr2_slow(double *X, double *Y, int n,
              double *mean_x, double *mean_y,
              double *var_x, double *var_y) {
    double sum_x = 0.0;
    for (int i = 0; i < n; i++) sum_x += X[i];
    *mean_x = sum_x / n;

    double sum_y = 0.0;
    for (int i = 0; i < n; i++) sum_y += Y[i];
    *mean_y = sum_y / n;

    double var_sum_x = 0.0;
    for (int i = 0; i < n; i++) {
        double diff = X[i] - *mean_x;
        var_sum_x += diff * diff;
    }
    *var_x = var_sum_x / n;

    double var_sum_y = 0.0;
    for (int i = 0; i < n; i++) {
        double diff = Y[i] - *mean_y;
        var_sum_y += diff * diff;
    }
    *var_y = var_sum_y / n;
}""",
        fast_code="""
void hr2_fast(double *X, double *Y, int n,
              double *mean_x, double *mean_y,
              double *var_x, double *var_y) {
    double sx = 0.0, sy = 0.0;
    for (int i = 0; i < n; i++) {
        sx += X[i];
        sy += Y[i];
    }
    *mean_x = sx / n;
    *mean_y = sy / n;

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
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *X = malloc(n * sizeof(double));
    double *Y = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) {
        X[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);
        Y[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);
    }
    double mx, my, vx, vy;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(X, Y, n, &mx, &my, &vx, &vy);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    /* compute expected independently */
    double sx = 0.0, sy = 0.0;
    for (int i = 0; i < n; i++) { sx += X[i]; sy += Y[i]; }
    double emx = sx / n, emy = sy / n;
    double evx = 0.0, evy = 0.0;
    for (int i = 0; i < n; i++) {
        double dx = X[i] - emx, dy = Y[i] - emy;
        evx += dx * dx; evy += dy * dy;
    }
    evx /= n; evy /= n;

    int correct = _bench_close(mx, emx, 1e-9, 1e-6)
               && _bench_close(my, emy, 1e-9, 1e-6)
               && _bench_close(vx, evx, 1e-9, 1e-6)
               && _bench_close(vy, evy, 1e-9, 1e-6);
    printf("result=%.10f time_ms=%.4f correct=%d\\n", mx, ms, correct);
    free(X); free(Y);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="HR-3",
        category="Human-Style Antipatterns",
        name="Dead / Debug Code",
        compiler_difficulty="High",
        description="volatile debug_counter++, NaN checks, and overflow checks inside a hot loop — "
                    "volatile prevents the compiler from removing them. "
                    "Strip all debug instrumentation from the production path.",
        slow_code="""
#include <stdio.h>
static volatile int debug_counter = 0;

void hr3_slow(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        debug_counter++;
        if (in[i] != in[i]) {
            fprintf(stderr, "Warning: NaN at index %d\\n", i);
        }
        out[i] = in[i] * 2.0 + 1.0;
        if (out[i] < -1e15 || out[i] > 1e15) {
            fprintf(stderr, "Warning: output overflow at %d\\n", i);
        }
    }
}""",
        fast_code="""
void hr3_fast(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * 2.0 + 1.0;
    }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *in  = malloc(n * sizeof(double));
    double *out = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++)
        in[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, in, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        double expected = in[i] * 2.0 + 1.0;
        if (!_bench_close(out[i], expected, 1e-9, 1e-6)) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(in); free(out);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="HR-4",
        category="Human-Style Antipatterns",
        name="Overly Defensive Checks",
        compiler_difficulty="Medium",
        description="arr == NULL, n <= 0, i < 0 || i >= n, and per-element NaN checks inside a loop "
                    "that already guarantees they're false. Check once before the loop; "
                    "remove all redundant per-iteration guards.",
        slow_code="""
double hr4_slow(double *arr, int n) {
    if (arr == NULL) return 0.0;
    if (n <= 0) return 0.0;

    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        double val = arr[i];
        if (val != val) continue;
        sum += val;
    }
    return sum;
}""",
        fast_code="""
double hr4_fast(double *arr, int n) {
    if (arr == NULL || n <= 0) return 0.0;

    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *arr = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++)
        arr[i] = ((double)rand() / RAND_MAX);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double result = optimized(arr, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    double expected = 0.0;
    for (int i = 0; i < n; i++) expected += arr[i];
    int correct = _bench_close(result, expected, 1e-9, 1e-9);
    printf("result=%.10f time_ms=%.4f correct=%d\\n", result, ms, correct);
    free(arr);
    return 0;
}"""
    ),
]
