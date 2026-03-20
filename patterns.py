from dataclasses import dataclass


@dataclass
class PatternEntry:
    pattern_id: str          # e.g., "SR-1"
    category: str            # e.g., "Semantic Redundancy"
    name: str                # e.g., "Loop-Invariant Semantic Computation"
    slow_code: str           # The inefficient C code
    fast_code: str           # Hand-optimized reference
    test_harness: str        # Code to call and verify the function
    compiler_difficulty: str  # "Low", "Medium", "High", "Very High"
    description: str         # What the inefficiency is

# All 27 patterns
PATTERNS = [
    # ── CATEGORY 1: Semantic Redundancy ──
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
        if (fabs(arr[i] - expected[i]) / fmax(fabs(expected[i]), 1e-12) > 1e-6) {
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
    double err = fabs(result - expected) / fmax(fabs(expected), 1e-12);

    printf("result=%.10f time_ms=%.4f correct=%d\\n", result, ms, err < 1e-4);
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
        if (fabs(result[i] - expected_i) / fmax(fabs(expected_i), 1e-12) > 1e-6) {
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
        if (fabs(arr[i] - expected[i]) / fmax(fabs(expected[i]), 1e-12) > 1e-6) {
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
        if (fabs(out[i] - expected) / fmax(fabs(expected), 1e-12) > 1e-9) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(data); free(out); free(w);
    return 0;
}"""
    ),

    # ── CATEGORY 2: Input-Sensitive ──
    PatternEntry(
        pattern_id="IS-1",
        category="Input-Sensitive Inefficiency",
        name="Sparse Data Redundancy",
        compiler_difficulty="Very High",
        description="Weight update `w[k][j] += delta[j]*layer[k]` processes all "
                    "elements even when 90% are zero. Add zero-skip guards.",
        slow_code="""
void is1_slow(double *w, double *delta, double *layer, int nj, int nk) {
    for (int k = 0; k < nk; k++) {
        for (int j = 0; j < nj; j++) {
            double new_dw = delta[j] * layer[k];
            w[k * nj + j] += new_dw;
        }
    }
}""",
        fast_code="""
void is1_fast(double *w, double *delta, double *layer, int nj, int nk) {
    for (int k = 0; k < nk; k++) {
        if (layer[k] == 0.0) continue;
        for (int j = 0; j < nj; j++) {
            if (delta[j] == 0.0) continue;
            w[k * nj + j] += delta[j] * layer[k];
        }
    }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int nj = 512, nk = 512;
    double *w        = calloc(nk * nj, sizeof(double));
    double *expected = calloc(nk * nj, sizeof(double));
    double *delta    = calloc(nj, sizeof(double));
    double *layer    = calloc(nk, sizeof(double));
    srand(42);
    for (int j = 0; j < nj; j++)
        delta[j] = (rand() % 10 == 0) ? ((double)rand() / RAND_MAX) : 0.0;
    for (int k = 0; k < nk; k++)
        layer[k] = (rand() % 10 == 0) ? ((double)rand() / RAND_MAX) : 0.0;

    for (int k = 0; k < nk; k++)
        for (int j = 0; j < nj; j++)
            expected[k * nj + j] += delta[j] * layer[k];

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(w, delta, layer, nj, nk);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < nk * nj; i++) {
        if (fabs(w[i] - expected[i]) / fmax(fabs(expected[i]), 1e-12) > 1e-6) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", w[0], ms, correct);
    free(w); free(expected); free(delta); free(layer);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="IS-2",
        category="Input-Sensitive Inefficiency",
        name="Unconditional Expensive Call on Skewed Data",
        compiler_difficulty="Very High",
        description="soft_clip() (containing log()) is called unconditionally for every "
                    "element, even though 99% are within threshold and the result is "
                    "discarded via ternary. Because soft_clip is noinline, the compiler "
                    "cannot eliminate the dead call. Add a branch guard so the expensive "
                    "path only runs for the 1% outliers.",
        slow_code="""
#include <math.h>
/* soft gradient clipping — noinline so compiler cannot eliminate dead calls */
static double __attribute__((noinline)) soft_clip(double val, double thresh) {
    double sign = (val >= 0.0) ? 1.0 : -1.0;
    return sign * (thresh + log(1.0 + fabs(val) - thresh));
}
void is2_slow(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        double clipped = soft_clip(val, thresh);        /* always called */
        out[i] = (fabs(val) > thresh) ? clipped : val; /* but only used 1% of the time */
    }
}""",
        fast_code="""
#include <math.h>
static double __attribute__((noinline)) soft_clip(double val, double thresh) {
    double sign = (val >= 0.0) ? 1.0 : -1.0;
    return sign * (thresh + log(1.0 + fabs(val) - thresh));
}
void is2_fast(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        if (fabs(val) > thresh)         /* guard: only call for the 1% outliers */
            out[i] = soft_clip(val, thresh);
        else
            out[i] = val;
    }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 5000000;
    double *in  = malloc(n * sizeof(double));
    double *out = malloc(n * sizeof(double));
    double thresh = 1.0;
    srand(42);
    for (int i = 0; i < n; i++) {
        if (rand() % 100 == 0)
            in[i] = 1.5 + 3.5 * ((double)rand() / RAND_MAX);  /* 1% outliers > thresh */
        else
            in[i] = -0.9 + 1.8 * ((double)rand() / RAND_MAX); /* 99% within thresh */
        if (rand() % 2) in[i] = -in[i];                        /* random sign */
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, in, n, thresh);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        double val = in[i], sign = (val >= 0) ? 1.0 : -1.0;
        double abs_val = fabs(val);
        double expected_i = (abs_val > thresh)
            ? sign * (thresh + log(1.0 + abs_val - thresh))
            : val;
        if (fabs(out[i] - expected_i) / fmax(fabs(expected_i), 1e-12) > 1e-6) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(in); free(out);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="IS-3",
        category="Input-Sensitive Inefficiency",
        name="Early Termination",
        compiler_difficulty="High",
        description="Counting all violations when only need to know if any exist. "
                    "Early return on first violation.",
        slow_code="""
int is3_slow(double *arr, int n, double threshold) {
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] > threshold) count++;
    }
    return count == 0;
}""",
        fast_code="""
int is3_fast(double *arr, int n, double threshold) {
    for (int i = 0; i < n; i++) {
        if (arr[i] > threshold) return 0;
    }
    return 1;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *arr = malloc(n * sizeof(double));
    double thresh = 0.5;
    srand(42);
    for (int i = 0; i < n; i++)
        arr[i] = (double)rand() / RAND_MAX;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int result = optimized(arr, n, thresh);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int violations = 0;
    for (int i = 0; i < n; i++) if (arr[i] > thresh) violations++;
    int expected = (violations == 0) ? 1 : 0;
    printf("result=%d time_ms=%.4f correct=%d\\n", result, ms, result == expected);
    free(arr);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="IS-4",
        category="Input-Sensitive Inefficiency",
        name="Sorted Input Exploitation",
        compiler_difficulty="Very High",
        description="Always running O(n log n) sort even when input is already sorted. "
                    "Check sorted first in O(n).",
        slow_code="""
#include <stdlib.h>
static int cmp_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}
void is4_slow(int *arr, int n) {
    qsort(arr, n, sizeof(int), cmp_int);
}""",
        fast_code="""
#include <stdlib.h>
static int cmp_int(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}
void is4_fast(int *arr, int n) {
    int sorted = 1;
    for (int i = 1; i < n; i++) {
        if (arr[i] < arr[i-1]) { sorted = 0; break; }
    }
    if (!sorted) qsort(arr, n, sizeof(int), cmp_int);
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static int _ref_cmp(const void *a, const void *b) { return (*(int*)a - *(int*)b); }

// LLM_CODE_HERE

int main() {
    int n = 5000000;
    int *arr = malloc(n * sizeof(int));
    int *expected = malloc(n * sizeof(int));
    srand(42);
    for (int i = 0; i < n; i++) arr[i] = expected[i] = i + (rand() % 3 == 0 ? -1 : 0);

    int tmp = arr[n/2]; arr[n/2] = arr[n/2 - 1]; arr[n/2 - 1] = tmp;
    tmp = expected[n/2]; expected[n/2] = expected[n/2-1]; expected[n/2-1] = tmp;

    qsort(expected, n, sizeof(int), _ref_cmp);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(arr, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (arr[i] != expected[i]) { correct = 0; break; }
    }
    printf("result=%d time_ms=%.4f correct=%d\\n", arr[0], ms, correct);
    free(arr); free(expected);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="IS-5",
        category="Input-Sensitive Inefficiency",
        name="Runtime Alias Check for Restrict Fast-Path",
        compiler_difficulty="Very High",
        description="Compiler must emit conservative aliasing-safe code because it can't prove at "
                    "compile time that out, A, B don't overlap. Check pointer ranges once at runtime; "
                    "if non-overlapping (the common case), dispatch to a __restrict__-qualified kernel "
                    "the compiler can freely vectorize.",
        slow_code="""
/* noinline forces compiler to compile conservatively: can't prove A, B, out don't overlap */
__attribute__((noinline))
void is5_slow(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
    }
}""",
        fast_code="""
static void __attribute__((noinline))
is5_restrict_kernel(double * __restrict__ out,
                    const double * __restrict__ A,
                    const double * __restrict__ B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
    }
}

void is5_fast(double *out, double *A, double *B, int n) {
    int no_alias = (out + n <= A || A + n <= out) &&
                   (out + n <= B || B + n <= out);
    if (no_alias) {
        is5_restrict_kernel(out, A, B, n);
    } else {
        for (int i = 0; i < n; i++) {
            out[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
        }
    }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 5000000;
    double *A        = malloc(n * sizeof(double));
    double *B        = malloc(n * sizeof(double));
    double *out      = malloc(n * sizeof(double));
    double *expected = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) {
        A[i] = 0.5 + 4.5 * ((double)rand() / RAND_MAX);
        B[i] = 0.5 + 4.5 * ((double)rand() / RAND_MAX);
        expected[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (fabs(out[i] - expected[i]) / fmax(fabs(expected[i]), 1e-12) > 1e-9) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(A); free(B); free(out); free(expected);
    return 0;
}"""
    ),

    # ── CATEGORY 3: Control-Flow ──
    PatternEntry(pattern_id="CF-3", category="Control-Flow", name="Vectorization-Hostile Conditional",
        compiler_difficulty="High",
        description="A noinline function wraps a computation with a runtime guard (always true "
                    "for this data). Verify the invariant once, then use an inline branch-free loop.",
        slow_code="""
static double __attribute__((noinline)) cf3_guarded(double x) {
    return x > 0.0 ? x * x + x * 0.5 : 0.0;
}
void cf3_slow(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) out[i] = cf3_guarded(in[i]);
}""",
        fast_code="""
void cf3_fast(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) out[i] = in[i] * in[i] + in[i] * 0.5;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

static double __attribute__((noinline)) cf3_guarded(double x) {
    return x > 0.0 ? x * x + x * 0.5 : 0.0;
}

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *in  = malloc(n * sizeof(double));
    double *out = malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) in[i] = (double)(i % 100 + 1) * 0.1;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, in, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        double expected = in[i] * in[i] + in[i] * 0.5;
        if (fabs(out[i] - expected) > 1e-9) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(in); free(out);
    return 0;
}"""
    ),

    PatternEntry(pattern_id="CF-4", category="Control-Flow", name="Function Pointer Dispatch in Hot Loop",
        compiler_difficulty="High",
        description="Per-element indirect call through a function pointer (or noinline dispatch) "
                    "prevents vectorization. Identify the concrete function at runtime and "
                    "dispatch to an inline tight loop.",
        slow_code="""
typedef double (*TransformFn)(double);
static double __attribute__((noinline)) fn_scale(double x) { return x * 1.5; }
static double __attribute__((noinline)) fn_square(double x) { return x * x; }
static double __attribute__((noinline)) fn_shift(double x)  { return x + 1.0; }
void cf4_slow(double *out, double *in, int n, TransformFn fn) {
    for (int i = 0; i < n; i++) out[i] = fn(in[i]);
}""",
        fast_code="""
void cf4_fast(double *out, double *in, int n, TransformFn fn) {
    if      (fn == fn_scale)  { for (int i=0;i<n;i++) out[i]=in[i]*1.5; }
    else if (fn == fn_square) { for (int i=0;i<n;i++) out[i]=in[i]*in[i]; }
    else if (fn == fn_shift)  { for (int i=0;i<n;i++) out[i]=in[i]+1.0; }
    else                      { for (int i=0;i<n;i++) out[i]=fn(in[i]); }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef double (*TransformFn)(double);
static double __attribute__((noinline)) fn_scale(double x)  { return x * 1.5; }
static double __attribute__((noinline)) fn_square(double x) { return x * x; }
static double __attribute__((noinline)) fn_shift(double x)  { return x + 1.0; }

// LLM_CODE_HERE

int main() {
    int n = 10000000;
    double *in  = malloc(n * sizeof(double));
    double *out = malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) in[i] = (double)(i % 200 + 1) * 0.05;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, in, n, fn_scale);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (fabs(out[i] - in[i] * 1.5) > 1e-9) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(in); free(out);
    return 0;
}"""
    ),

    # ── CATEGORY 4: Human-Style Antipatterns ──
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

    int correct = fabs(mx - emx) < 1e-9 && fabs(my - emy) < 1e-9
               && fabs(vx - evx) / fmax(fabs(evx), 1e-12) < 1e-6
               && fabs(vy - evy) / fmax(fabs(evy), 1e-12) < 1e-6;
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
        if (fabs(out[i] - expected) > 1e-9) { correct = 0; break; }
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
    int correct = fabs(result - expected) / fmax(fabs(expected), 1e-12) < 1e-9;
    printf("result=%.10f time_ms=%.4f correct=%d\\n", result, ms, correct);
    free(arr);
    return 0;
}"""
    ),

    # ── CATEGORY 5: Data Structure ──
    PatternEntry(
        pattern_id="DS-1",
        category="Data Structure",
        name="Linear Search vs Hash Lookup",
        compiler_difficulty="Very High",
        description="O(n) linear scan through 50 000-entry array for each of many queries. "
                    "Pre-build an open-addressing hash table; each lookup is O(1).",
        slow_code="""
int ds1_slow_lookup(int *keys, int *values, int n, int target) {
    for (int i = 0; i < n; i++) {
        if (keys[i] == target) return values[i];
    }
    return -1;
}""",
        fast_code="""
#define HT_SIZE 65536
#define HT_MASK (HT_SIZE - 1)
typedef struct { int key; int value; int occupied; } HTEntry;

void ds1_build_ht(HTEntry *ht, int *keys, int *values, int n) {
    memset(ht, 0, HT_SIZE * sizeof(HTEntry));
    for (int i = 0; i < n; i++) {
        int h = (unsigned int)keys[i] & HT_MASK;
        while (ht[h].occupied) h = (h + 1) & HT_MASK;
        ht[h].key = keys[i];
        ht[h].value = values[i];
        ht[h].occupied = 1;
    }
}

int ds1_fast_lookup(HTEntry *ht, int target) {
    int h = (unsigned int)target & HT_MASK;
    while (ht[h].occupied) {
        if (ht[h].key == target) return ht[h].value;
        h = (h + 1) & HT_MASK;
    }
    return -1;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define HT_SIZE 65536
#define HT_MASK (HT_SIZE - 1)
typedef struct { int key; int value; int occupied; } HTEntry;

static int ds1_slow_lookup(int *keys, int *values, int n, int target) {
    for (int i = 0; i < n; i++) {
        if (keys[i] == target) return values[i];
    }
    return -1;
}

// LLM_CODE_HERE

int main() {
    int n_keys = 50000;
    int n_queries = 1000;
    int *keys    = malloc(n_keys * sizeof(int));
    int *values  = malloc(n_keys * sizeof(int));
    int *queries = malloc(n_queries * sizeof(int));
    srand(42);
    for (int i = 0; i < n_keys; i++) {
        keys[i]   = i * 7 + 13;
        values[i] = i * 3;
    }
    for (int i = 0; i < n_queries; i++)
        queries[i] = keys[rand() % n_keys];

    /* build hash table for fast version */
    HTEntry *ht = malloc(HT_SIZE * sizeof(HTEntry));
    ds1_build_ht(ht, keys, values, n_keys);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int sum_fast = 0;
    for (int i = 0; i < n_queries; i++)
        sum_fast += optimized(ht, queries[i]);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int sum_slow = 0;
    for (int i = 0; i < n_queries; i++)
        sum_slow += ds1_slow_lookup(keys, values, n_keys, queries[i]);

    int correct = (sum_slow == sum_fast);
    printf("result=%d time_ms=%.4f correct=%d\\n", sum_fast, ms, correct);
    free(keys); free(values); free(queries); free(ht);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="DS-2",
        category="Data Structure",
        name="Repeated Allocation vs Pre-allocation",
        compiler_difficulty="High",
        description="malloc / free per chunk inside the processing loop. "
                    "Allocate the temp buffer once before the loop; reuse it.",
        slow_code="""
#include <stdlib.h>
void ds2_slow(double *results, double *input, int n, int chunk_size) {
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        double *temp = malloc(sz * sizeof(double));
        for (int j = 0; j < sz; j++) temp[j] = input[i + j] * input[i + j];
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk_size] = sum;
        free(temp);
    }
}""",
        fast_code="""
#include <stdlib.h>
void ds2_fast(double *results, double *input, int n, int chunk_size) {
    double *temp = malloc(chunk_size * sizeof(double));
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        for (int j = 0; j < sz; j++) temp[j] = input[i + j] * input[i + j];
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk_size] = sum;
    }
    free(temp);
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 5000000;
    int chunk_size = 1024;
    int n_results = n / chunk_size + 1;
    double *input    = malloc(n * sizeof(double));
    double *out      = malloc(n_results * sizeof(double));
    double *expected = malloc(n_results * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++)
        input[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);

    /* compute expected */
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += input[i+j] * input[i+j];
        expected[i / chunk_size] = sum;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, input, n, chunk_size);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n_results; i++) {
        if (fabs(out[i] - expected[i]) / fmax(fabs(expected[i]), 1e-12) > 1e-9) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(input); free(out); free(expected);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="DS-3",
        category="Data Structure",
        name="Unnecessary Copying (pass-by-value)",
        compiler_difficulty="Medium",
        description="512-byte BigStruct copied onto the stack for every call to the processing function. "
                    "Pass by const * — only the pointer is copied.",
        slow_code="""
typedef struct {
    double data[64];
    int size;
} BigStruct;

double ds3_slow_process(BigStruct s) {
    double sum = 0.0;
    for (int i = 0; i < s.size; i++) sum += s.data[i];
    return sum;
}""",
        fast_code="""
typedef struct {
    double data[64];
    int size;
} BigStruct;

double ds3_fast_process(const BigStruct *s) {
    double sum = 0.0;
    for (int i = 0; i < s->size; i++) sum += s->data[i];
    return sum;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct {
    double data[64];
    int size;
} BigStruct;

static double ds3_slow_process(BigStruct s) {
    double sum = 0.0;
    for (int i = 0; i < s.size; i++) sum += s.data[i];
    return sum;
}

// LLM_CODE_HERE

int main() {
    int n = 2000000;
    BigStruct *arr = malloc(n * sizeof(BigStruct));
    srand(42);
    for (int i = 0; i < n; i++) {
        arr[i].size = 64;
        for (int j = 0; j < 64; j++) arr[i].data[j] = (double)(i + j);
    }

    double ref_result = 0.0;
    for (int i = 0; i < n; i++) ref_result += ds3_slow_process(arr[i]);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double fast_result = 0.0;
    for (int i = 0; i < n; i++) fast_result += optimized(&arr[i]);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = fabs(ref_result - fast_result) / fmax(fabs(ref_result), 1e-12) < 1e-6;
    printf("result=%.10f time_ms=%.4f correct=%d\\n", fast_result, ms, correct);
    free(arr);
    return 0;
}"""
    ),

    PatternEntry(pattern_id="DS-4", category="Data Structure", name="AoS vs SoA Cache Access",
        compiler_difficulty="Very High",
        description="Array of Structures causes 64-byte stride when accessing one field. "
                    "Structure of Arrays gives sequential 8-byte stride.",
        slow_code="""
typedef struct { double x,y,z,vx,vy,vz,mass,charge; } Particle;
double ds4_slow(Particle *p, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += p[i].mass;
    return total;
}""",
        fast_code="""
double ds4_fast(double *mass, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct { double x,y,z,vx,vy,vz,mass,charge; } Particle;

static double ds4_slow_ref(Particle *p, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += p[i].mass;
    return total;
}

// LLM_CODE_HERE

int main() {
    int n = 5000000;
    Particle *p = malloc(n * sizeof(Particle));
    double *mass = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) {
        p[i].x = p[i].y = p[i].z = p[i].vx = p[i].vy = p[i].vz = p[i].charge = 1.0;
        p[i].mass = (double)rand() / RAND_MAX;
        mass[i] = p[i].mass;
    }

    double expected = ds4_slow_ref(p, n);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double result = optimized(mass, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    double err = fabs(result - expected) / fmax(fabs(expected), 1e-12);
    printf("result=%.10f time_ms=%.4f correct=%d\\n", result, ms, err < 1e-6);
    free(p); free(mass);
    return 0;
}"""
    ),

    PatternEntry(pattern_id="AL-1", category="Algorithmic", name="Brute Force vs Memoization/DP",
        compiler_difficulty="Very High",
        description="O(2^n) recursive Fibonacci vs O(n) iterative. "
                    "Compiler cannot transform recursion into DP.",
        slow_code="""
long long al1_slow(int n) {
    if (n <= 1) return n;
    return al1_slow(n-1) + al1_slow(n-2);
}""",
        fast_code="""
long long al1_fast(int n) {
    if (n <= 1) return n;
    long long a=0, b=1;
    for (int i=2; i<=n; i++) { long long t=a+b; a=b; b=t; }
    return b;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 40;
    long long expected = 102334155LL;

    /* Warm up + timed loop so fast O(n) code still registers */
    optimized(n);
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    long long result = 0;
    for (int rep = 0; rep < 100000; rep++) result = optimized(n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    printf("result=%lld time_ms=%.4f correct=%d\\n", result, ms, result == expected);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="AL-2",
        category="Algorithmic",
        name="Repeated Sort vs Sorted Insertion",
        compiler_difficulty="Very High",
        description="Re-qsort the entire array after every insertion — O(n^2 log n) total. "
                    "Binary-search for the insertion point, memmove to make room — O(n^2) total "
                    "but with much smaller constant.",
        slow_code="""
#include <stdlib.h>
#include <string.h>
static int cmp_double(const void *a, const void *b) {
    double da = *(const double*)a, db = *(const double*)b;
    return (da > db) - (da < db);
}
void al2_slow(double *arr, int *size, double *items, int n_items) {
    *size = 0;
    for (int i = 0; i < n_items; i++) {
        arr[*size] = items[i];
        (*size)++;
        qsort(arr, *size, sizeof(double), cmp_double);
    }
}""",
        fast_code="""
#include <stdlib.h>
#include <string.h>
static int cmp_double(const void *a, const void *b) {
    double da = *(const double*)a, db = *(const double*)b;
    return (da > db) - (da < db);
}
static int binary_search_insert(double *arr, int size, double val) {
    int lo = 0, hi = size;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (arr[mid] < val) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
void al2_fast(double *arr, int *size, double *items, int n_items) {
    *size = 0;
    for (int i = 0; i < n_items; i++) {
        int pos = binary_search_insert(arr, *size, items[i]);
        memmove(&arr[pos + 1], &arr[pos], (*size - pos) * sizeof(double));
        arr[pos] = items[i];
        (*size)++;
    }
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

static int cmp_d(const void *a, const void *b) {
    double da = *(const double*)a, db = *(const double*)b;
    return (da > db) - (da < db);
}

// LLM_CODE_HERE

int main() {
    int n_items = 10000;
    double *items    = malloc(n_items * sizeof(double));
    double *arr      = malloc(n_items * sizeof(double));
    double *expected = malloc(n_items * sizeof(double));
    srand(42);
    for (int i = 0; i < n_items; i++)
        items[i] = ((double)rand() / RAND_MAX) * 1000.0;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int sz = 0;
    optimized(arr, &sz, items, n_items);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    /* compute expected by sorting a copy */
    memcpy(expected, items, n_items * sizeof(double));
    qsort(expected, n_items, sizeof(double), cmp_d);

    int correct = (sz == n_items);
    for (int i = 0; i < n_items && correct; i++)
        if (fabs(arr[i] - expected[i]) > 1e-12) correct = 0;
    printf("result=%.10f time_ms=%.4f correct=%d\\n", arr[0], ms, correct);
    free(items); free(arr); free(expected);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="AL-3",
        category="Algorithmic",
        name="Naive vs KMP Pattern Matching",
        compiler_difficulty="High",
        description="O(n*m) brute-force search for a pattern in a text. "
                    "Knuth-Morris-Pratt: build failure function in O(m), then scan in O(n).",
        slow_code="""
int al3_slow(int *text, int tn, int *pattern, int pn) {
    int count = 0;
    for (int i = 0; i <= tn - pn; i++) {
        int match = 1;
        for (int j = 0; j < pn; j++) {
            if (text[i + j] != pattern[j]) { match = 0; break; }
        }
        if (match) count++;
    }
    return count;
}""",
        fast_code="""
#include <stdlib.h>
static void build_failure(int *pattern, int pn, int *fail) {
    fail[0] = 0;
    int k = 0;
    for (int i = 1; i < pn; i++) {
        while (k > 0 && pattern[k] != pattern[i]) k = fail[k - 1];
        if (pattern[k] == pattern[i]) k++;
        fail[i] = k;
    }
}
int al3_fast(int *text, int tn, int *pattern, int pn) {
    int *fail = malloc(pn * sizeof(int));
    build_failure(pattern, pn, fail);
    int count = 0, k = 0;
    for (int i = 0; i < tn; i++) {
        while (k > 0 && pattern[k] != text[i]) k = fail[k - 1];
        if (pattern[k] == text[i]) k++;
        if (k == pn) { count++; k = fail[k - 1]; }
    }
    free(fail);
    return count;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int tn = 10000000;
    int pn = 8;
    int *text    = malloc(tn * sizeof(int));
    int pattern[8] = {3, 1, 4, 1, 5, 9, 2, 6};
    srand(42);
    for (int i = 0; i < tn; i++) text[i] = rand() % 10;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int result = optimized(text, tn, pattern, pn);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    /* brute-force reference */
    int expected = 0;
    for (int i = 0; i <= tn - pn; i++) {
        int match = 1;
        for (int j = 0; j < pn; j++) if (text[i+j] != pattern[j]) { match = 0; break; }
        if (match) expected++;
    }
    printf("result=%d time_ms=%.4f correct=%d\\n", result, ms, result == expected);
    free(text);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="AL-4",
        category="Algorithmic",
        name="Recursive vs DP (Grid Paths)",
        compiler_difficulty="Very High",
        description="Exponential recursive path counting — recomputes overlapping sub-grids. "
                    "O(r*c) DP table (O(c) space) — no redundant recomputation.",
        slow_code="""
long long al4_slow(int r, int c) {
    if (r == 0 || c == 0) return 1;
    return al4_slow(r - 1, c) + al4_slow(r, c - 1);
}""",
        fast_code="""
#include <stdlib.h>
long long al4_fast(int r, int c) {
    long long *dp = calloc(c + 1, sizeof(long long));
    for (int j = 0; j <= c; j++) dp[j] = 1;
    for (int i = 1; i <= r; i++) {
        for (int j = 1; j <= c; j++) dp[j] += dp[j - 1];
    }
    long long result = dp[c];
    free(dp);
    return result;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int r = 18, c = 18;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    long long result = 0;
    for (int rep = 0; rep < 100000; rep++) result = optimized(r, c);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    /* expected: C(36,18) = 9075135300 */
    long long expected = 9075135300LL;
    printf("result=%lld time_ms=%.4f correct=%d\\n", result, ms, result == expected);
    return 0;
}"""
    ),

    # ── CATEGORY 7: Memory / IO ──
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
    int correct = fabs(result - expected) / fmax(fabs(expected), 1e-12) < 1e-6;
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
        if (fabs(out[i] - (A[i] + B[i])) > 1e-12) { correct = 0; break; }
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
    int correct = fabs(result - expected) / fmax(fabs(expected), 1e-12) < 1e-6;
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
        if (fabs(mat[i] - expected[i]) > 1e-9) { correct = 0; break; }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", mat[0], ms, correct);
    free(mat); free(expected);
    return 0;
}"""
    ),
]
