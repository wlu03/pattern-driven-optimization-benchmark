# Semantic Redundancy patterns: SR-1 through SR-5.
from ._entry import PatternEntry


SR_PATTERNS = [
    PatternEntry(
        pattern_id="SR-1",
        category="Semantic Redundancy",
        name="Loop-Invariant Function Call (Log Series)",
        compiler_difficulty="Very High",
        description="A log-series calibration function with loop-invariant arguments "
                    "is called on every iteration. The compiler cannot hoist it because "
                    "the inner transcendental loop prevents const/pure analysis. "
                    "Hoist once before the loop.",
        slow_code="""
#include <math.h>
/* 40-term log series — transcendental inner loop blocks compiler hoisting */
static double log_series(double base) {
    double r = 0.0;
    for (int k = 1; k <= 40; k++) r += log(base * k + 1.0) / k;
    return r;
}
void sr1_slow(double *arr, int n, double base) {
    for (int i = 0; i < n; i++)
        arr[i] *= log_series(base);  /* same result every iteration */
}""",
        fast_code="""
#include <math.h>
static double log_series(double base) {
    double r = 0.0;
    for (int k = 1; k <= 40; k++) r += log(base * k + 1.0) / k;
    return r;
}
void sr1_fast(double *arr, int n, double base) {
    double scale = log_series(base);  /* hoisted once */
    for (int i = 0; i < n; i++) arr[i] *= scale;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 1000000;
    double base = 1.5;
    double *arr      = malloc(n * sizeof(double));
    double *expected = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++)
        arr[i] = expected[i] = 0.5 + ((double)rand() / RAND_MAX);

    /* compute scale inline — independent of LLM code */
    double scale = 0.0;
    for (int k = 1; k <= 40; k++) scale += log(base * k + 1.0) / k;
    for (int i = 0; i < n; i++) expected[i] *= scale;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(arr, n, base);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0
              + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (!_bench_close(arr[i], expected[i], 1e-9, 1e-6)) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", arr[0], ms, correct);
    free(arr); free(expected);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="SR-2",
        category="Semantic Redundancy",
        name="Loop-Invariant Term in Mixed Expression",
        compiler_difficulty="Very High",
        description="Loop body contains `alpha*X[i]*X[i] + beta*Y[i] + penalty(alpha,beta)` "
                    "where penalty() has a transcendental inner loop with loop-invariant arguments. "
                    "Optimization: separate accumulators for data-dependent terms, "
                    "call penalty once and multiply by n.",
        slow_code="""
#include <math.h>
/* regularization penalty — sin/exp inner loop blocks compiler hoisting */
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
}""",
        fast_code="""
#include <math.h>
static double penalty(double a, double b) {
    double r = 0.0;
    for (int k = 1; k <= 20; k++) r += sin(a * k) * exp(-b * k * 0.05);
    return r;
}
__attribute__((noinline))
double sr2_fast(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0.0, sumY = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY   += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (double)n * penalty(alpha, beta);
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 1000000;
    double *X = malloc(n * sizeof(double));
    double *Y = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) {
        X[i] = -5.0 + 10.0 * ((double)rand() / RAND_MAX);
        Y[i] = -5.0 + 10.0 * ((double)rand() / RAND_MAX);
    }
    double alpha = 2.5, beta = 1.5;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double result = optimized(X, Y, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    /* compute expected independently — penalty inlined in harness, no LLM dependency */
    double p = 0.0;
    for (int k = 1; k <= 20; k++) p += sin(alpha * k) * exp(-beta * k * 0.05);
    double expected = 0.0;
    for (int i = 0; i < n; i++)
        expected += alpha * X[i] * X[i] + beta * Y[i] + p;

    printf("result=%.10f time_ms=%.4f correct=%d\\n",
           result, ms, _bench_close(result, expected, 1e-6, 1e-4));
    free(X); free(Y);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="SR-3",
        category="Semantic Redundancy",
        name="Redundant Aggregation Recomputation",
        compiler_difficulty="Very High",
        description="Recomputing a running average from scratch each iteration "
                    "(O(n^2)) instead of maintaining a running sum (O(n)).",
        slow_code="""
void sr3_slow(double *data, double *running_avg, int n) {
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j <= i; j++) {
            sum += data[j];
        }
        running_avg[i] = sum / (i + 1);
    }
}""",
        fast_code="""
void sr3_fast(double *data, double *running_avg, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        running_avg[i] = sum / (i + 1);
    }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 20000;
    double *data = malloc(n * sizeof(double));
    double *result = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) data[i] = (double)rand() / RAND_MAX;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(data, result, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    double sum = 0.0;
    int correct = 1;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        double expected_i = sum / (i + 1);
        if (!_bench_close(result[i], expected_i, 1e-9, 1e-6)) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", result[n-1], ms, correct);
    free(data); free(result);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="SR-4",
        category="Semantic Redundancy",
        name="Invariant Function Call in Loop",
        compiler_difficulty="High",
        description="A pure function with loop-invariant arguments is called "
                    "every iteration. Compiler can't hoist across TU boundaries.",
        slow_code="""
#include <math.h>
double expensive_lookup(int key) {
    double r = 0.0;
    for (int i = 0; i < 100; i++)
        r += sin((double)(key+i)) * cos((double)(key-i));
    return r;
}
void sr4_slow(double *arr, int n, int config_key) {
    for (int i = 0; i < n; i++) {
        double factor = expensive_lookup(config_key);
        arr[i] *= factor;
    }
}""",
        fast_code="""
#include <math.h>
double expensive_lookup(int key) {
    double r = 0.0;
    for (int i = 0; i < 100; i++)
        r += sin((double)(key+i)) * cos((double)(key-i));
    return r;
}
void sr4_fast(double *arr, int n, int config_key) {
    double factor = expensive_lookup(config_key);
    for (int i = 0; i < n; i++) arr[i] *= factor;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 2000000;
    double *arr = malloc(n * sizeof(double));
    double *expected = malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) arr[i] = expected[i] = (double)(i % 100) * 0.01 + 0.1;
    int config_key = 7;

    double factor = 0.0;
    for (int i = 0; i < 100; i++)
        factor += sin((double)(config_key+i)) * cos((double)(config_key-i));
    for (int i = 0; i < n; i++) expected[i] *= factor;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(arr, n, config_key);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (!_bench_close(arr[i], expected[i], 1e-9, 1e-6)) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", arr[0], ms, correct);
    free(arr); free(expected);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="SR-5",
        category="Semantic Redundancy",
        name="Repeated Division by Loop-Invariant Denominator",
        compiler_difficulty="Very High",
        description="Each element is divided by a value that is loop-invariant but "
                    "computed by a function whose result GCC cannot hoist due to aliasing: "
                    "without restrict qualifiers, out[] could alias w[], so the compiler "
                    "must re-evaluate compute_norm each iteration. "
                    "Optimize: call once, precompute reciprocal, multiply.",
        slow_code="""
#include <math.h>
/* L2 norm — compiler cannot hoist: out[] may alias w[], making w loop-variant */
static double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    return sqrt(s);
}
__attribute__((noinline))
void sr5_slow(double *out, double *data, int n, double *w, int m) {
    for (int i = 0; i < n; i++)
        out[i] = data[i] / compute_norm(w, m);  /* recomputed every iteration */
}""",
        fast_code="""
#include <math.h>
static double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    return sqrt(s);
}
__attribute__((noinline))
void sr5_fast(double *out, double *data, int n, double *w, int m) {
    double inv = 1.0 / compute_norm(w, m);  /* hoist call + precompute reciprocal */
    for (int i = 0; i < n; i++) out[i] = data[i] * inv;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 1000000, m = 256;
    double *data = malloc(n * sizeof(double));
    double *out  = malloc(n * sizeof(double));
    double *w    = malloc(m * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) data[i] = -5.0 + 10.0 * ((double)rand() / RAND_MAX);
    for (int j = 0; j < m; j++) w[j]    = ((double)rand() / RAND_MAX);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, data, n, w, m);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    /* compute norm inline — independent of LLM */
    double s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    double norm = sqrt(s);

    int correct = 1;
    for (int i = 0; i < n; i++) {
        double expected = data[i] / norm;
        if (!_bench_close(out[i], expected, 1e-12, 1e-9)) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(data); free(out); free(w);
    return 0;
}"""
    ),
]
