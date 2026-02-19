// Correct but suboptimal algorithm choice. Compilers cannot change algorithms — only LLMs with semantic understanding can recognize a better approach.

#include "../harness/bench_harness.h"

// AL-1: Brute Force vs. Memoization/DP
long long al1_slow(int n) {
    if (n <= 1) return n;
    return al1_slow(n - 1) + al1_slow(n - 2);  // O(2^n)
}

long long al1_fast(int n) {
    if (n <= 1) return n;
    long long a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        long long tmp = a + b;
        a = b;
        b = tmp;
    }
    return b;  // O(n)
}

// AL-2: Repeated Sort vs. Sorted Insertion
// Sorting the entire array after every insertion instead of
// maintaining sorted order with binary insert
static int cmp_double(const void *a, const void *b) {
    double da = *(const double*)a, db = *(const double*)b;
    return (da > db) - (da < db);
}

void al2_slow(double *arr, int *size, double *items, int n_items) {
    *size = 0;
    for (int i = 0; i < n_items; i++) {
        arr[*size] = items[i];
        (*size)++;
        qsort(arr, *size, sizeof(double), cmp_double);  // Re-sort every time
    }
}

// Binary search for insert position
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
}


// AL-3: Naive String Matching vs. Efficient Search
// O(n*m) brute force vs. O(n+m) using KMP-style approach.
// (Using integer arrays to simulate pattern matching)
int al3_slow(int *text, int tn, int *pattern, int pn) {
    int count = 0;
    for (int i = 0; i <= tn - pn; i++) {
        int match = 1;
        for (int j = 0; j < pn; j++) {
            if (text[i + j] != pattern[j]) {
                match = 0;
                break;
            }
        }
        if (match) count++;
    }
    return count;
}

// Build failure function for KMP
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
        if (k == pn) {
            count++;
            k = fail[k - 1];
        }
    }
    free(fail);
    return count;
}


// AL-4: Redundant Recomputation in Recursion
// Computing overlapping subproblems without caching.
// Classic: grid path counting without memoization.

// Count paths in a grid from (0,0) to (r,c) moving only right or down
long long al4_slow(int r, int c) {
    if (r == 0 || c == 0) return 1;
    return al4_slow(r - 1, c) + al4_slow(r, c - 1);  // Exponential
}

long long al4_fast(int r, int c) {
    // DP table: O(r*c) time, O(c) space
    long long *dp = calloc(c + 1, sizeof(long long));
    for (int j = 0; j <= c; j++) dp[j] = 1;
    for (int i = 1; i <= r; i++) {
        for (int j = 1; j <= c; j++) {
            dp[j] += dp[j - 1];
        }
    }
    long long result = dp[c];
    free(dp);
    return result;
}


void run_algorithmic(void) {
    srand(42);

    // AL-1: Fibonacci
    {
        int fib_n = 40;  // Slow version takes ~1s for n=40
        BenchTimer t;
        long long r_slow, r_fast;

        timer_start(&t);
        r_slow = al1_slow(fib_n);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        for (int r = 0; r < 1000000; r++) r_fast = al1_fast(fib_n);
        double ms_fast = timer_stop(&t) / 1000000.0;

        int ok = (r_slow == r_fast);
        record_result("AL-1", "Brute Force vs Memoization/DP", ms_slow, ms_fast, ok);
        printf("[AL-1] Slow=%.2fms Fast=%.6fms Speedup=%.0fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }

    // AL-2: Repeated sort vs sorted insert
    {
        int n_items = 10000;
        double *items = malloc(n_items * sizeof(double));
        double *arr_slow = malloc(n_items * sizeof(double));
        double *arr_fast = malloc(n_items * sizeof(double));
        fill_random_double(items, n_items, 0.0, 1000.0);

        BenchTimer t;
        int sz_s, sz_f;

        timer_start(&t);
        al2_slow(arr_slow, &sz_s, items, n_items);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        al2_fast(arr_fast, &sz_f, items, n_items);
        double ms_fast = timer_stop(&t);

        int ok = (sz_s == sz_f) && verify_array_double(arr_slow, arr_fast, sz_s, 1e-12);
        record_result("AL-2", "Repeated Sort vs Sorted Insertion", ms_slow, ms_fast, ok);
        printf("[AL-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(items); free(arr_slow); free(arr_fast);
    }

    // AL-3: Pattern matching
    {
        int tn = 10000000;
        int pn = 8;
        int *text = malloc(tn * sizeof(int));
        int pattern[8] = {3, 1, 4, 1, 5, 9, 2, 6};
        fill_random_int(text, tn, 0, 9);

        BenchTimer t;
        int c_slow, c_fast;

        timer_start(&t);
        c_slow = al3_slow(text, tn, pattern, pn);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        c_fast = al3_fast(text, tn, pattern, pn);
        double ms_fast = timer_stop(&t);

        int ok = (c_slow == c_fast);
        record_result("AL-3", "Naive vs KMP Pattern Matching", ms_slow, ms_fast, ok);
        printf("[AL-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s (found=%d)\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL", c_slow);

        free(text);
    }

    // AL-4: Grid paths (recursive vs DP)
    {
        int r = 18, c = 18;  // Slow is exponential, keep small
        BenchTimer t;
        long long r_slow, r_fast;

        timer_start(&t);
        r_slow = al4_slow(r, c);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        for (int rep = 0; rep < 100000; rep++) r_fast = al4_fast(r, c);
        double ms_fast = timer_stop(&t) / 100000.0;

        int ok = (r_slow == r_fast);
        record_result("AL-4", "Recursive vs DP (grid paths)", ms_slow, ms_fast, ok);
        printf("[AL-4] Slow=%.2fms Fast=%.6fms Speedup=%.0fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");
    }
}
