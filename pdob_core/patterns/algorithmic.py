# Algorithmic patterns: AL-1 through AL-4.
from ._entry import PatternEntry


AL_PATTERNS = [
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
        if (!_bench_close(arr[i], expected[i], 1e-9, 1e-9)) correct = 0;
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
]
