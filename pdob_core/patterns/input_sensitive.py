# Input-Sensitive Inefficiency patterns: IS-1 through IS-5.
from ._entry import PatternEntry


IS_PATTERNS = [
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
    srand(_bench_seed(42));
    /* BENCH_DIST selects sparsity: "random" (default, 90% zeros — original),
       "sparse" (95% zeros — even sparser), "all_zero" (every elem zero,
       fast path should be a no-op), "sorted"/"reverse_sorted" (DENSE — zero
       skipping no longer helps, exposing the input-sensitivity of IS-1). */
    const char *_d = _bench_dist();
    int sparsity_pct;  /* probability (0..100) that an element is zero */
    if      (strcmp(_d, "all_zero") == 0)        sparsity_pct = 100;
    else if (strcmp(_d, "sparse") == 0)          sparsity_pct =  95;
    else if (strcmp(_d, "sorted") == 0)          sparsity_pct =   0;  /* fully dense */
    else if (strcmp(_d, "reverse_sorted") == 0)  sparsity_pct =   0;  /* fully dense */
    else                                          sparsity_pct =  90;  /* "random" */
    for (int j = 0; j < nj; j++)
        delta[j] = (rand() % 100 < sparsity_pct) ? 0.0 : ((double)rand() / RAND_MAX);
    for (int k = 0; k < nk; k++)
        layer[k] = (rand() % 100 < sparsity_pct) ? 0.0 : ((double)rand() / RAND_MAX);

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
        if (!_bench_close(w[i], expected[i], 1e-9, 1e-6)) {
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
    srand(_bench_seed(42));
    /* BENCH_DIST varies the fraction of outliers (the cost driver):
       "random" — 1% outliers (original; soft_clip rarely runs)
       "sparse" — 1% outliers (same, sparse = rare-event semantics)
       "sorted" / "reverse_sorted" — 0% outliers (worst case for slow path:
           soft_clip wastes effort for every elem)
       "all_zero" — 100% outliers (best case for slow path) */
    const char *_d = _bench_dist();
    int outlier_pct;
    if      (strcmp(_d, "all_zero") == 0)        outlier_pct = 100;
    else if (strcmp(_d, "sorted") == 0)          outlier_pct =   0;
    else if (strcmp(_d, "reverse_sorted") == 0)  outlier_pct =   0;
    else                                          outlier_pct =   1;  /* random/sparse */
    for (int i = 0; i < n; i++) {
        if (outlier_pct >= 100 || (outlier_pct > 0 && rand() % 100 < outlier_pct))
            in[i] = 1.5 + 3.5 * ((double)rand() / RAND_MAX);  /* outlier > thresh */
        else
            in[i] = -0.9 + 1.8 * ((double)rand() / RAND_MAX); /* within thresh */
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
        if (!_bench_close(out[i], expected_i, 1e-9, 1e-6)) {
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
    srand(_bench_seed(42));
    /* BENCH_DIST controls when the FIRST violation occurs (this is the
       cost driver for early-termination):
         "random"          — first violation expected ~halfway in (original)
         "all_zero"        — no violations: SLOW scans all n; FAST scans all n
                              (same cost; speedup ≈ 1x)
         "sorted"          — violation occurs LATE (near end) — small speedup
         "reverse_sorted"  — violation occurs IMMEDIATELY at i=0 — huge speedup
         "sparse"          — 95% zeros, 5% random in [0,1] (most below
                              thresh) — violation rare, similar to all_zero  */
    _bench_fill_dist(arr, n, 0.0, 1.0);

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
    srand(_bench_seed(42));
    /* BENCH_DIST is the input-sensitivity knob for IS-4:
         "random" (default) — original near-sorted-with-swap distribution
         "sorted"           — already sorted; FAST should detect and skip qsort
         "reverse_sorted"   — worst case; FAST must run qsort anyway
         "all_zero"         — all-equal (trivially sorted); FAST detects
         "sparse"           — 95% zeros + few outliers; nearly-sorted-ish    */
    const char *_d = _bench_dist();
    if (strcmp(_d, "sorted") == 0) {
        for (int i = 0; i < n; i++) arr[i] = expected[i] = i;
    } else if (strcmp(_d, "reverse_sorted") == 0) {
        for (int i = 0; i < n; i++) arr[i] = expected[i] = n - i;
    } else if (strcmp(_d, "all_zero") == 0) {
        for (int i = 0; i < n; i++) arr[i] = expected[i] = 0;
    } else if (strcmp(_d, "sparse") == 0) {
        for (int i = 0; i < n; i++) arr[i] = expected[i] = (rand() % 100 < 95) ? 0 : (rand() % 1000);
    } else { /* "random" default — original near-sorted-with-one-swap */
        for (int i = 0; i < n; i++) arr[i] = expected[i] = i + (rand() % 3 == 0 ? -1 : 0);
        int tmp = arr[n/2]; arr[n/2] = arr[n/2 - 1]; arr[n/2 - 1] = tmp;
        tmp = expected[n/2]; expected[n/2] = expected[n/2-1]; expected[n/2-1] = tmp;
    }

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
    srand(_bench_seed(42));
    /* BENCH_DIST varies the input distribution feeding the polynomial.
       The alias check itself isn't input-sensitive (out/A/B never overlap
       here), but seeding/dist changes give us cross-config diversity. */
    _bench_fill_dist(A, n, 0.5, 5.0);
    _bench_fill_dist(B, n, 0.5, 5.0);
    for (int i = 0; i < n; i++) {
        expected[i] = A[i] * A[i] + B[i] * 2.0 - A[i] * 0.5 + B[i] * B[i];
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n; i++) {
        if (!_bench_close(out[i], expected[i], 1e-12, 1e-9)) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(A); free(B); free(out); free(expected);
    return 0;
}"""
    ),
]
