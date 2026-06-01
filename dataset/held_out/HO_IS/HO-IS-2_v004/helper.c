#include <stdlib.h>
#include <string.h>

static int _adaptive_cmp_ho_is2(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

__attribute__((noinline))
void adaptive_sort_ho_is2_v004(int *arr, long n) {
    if (n <= 1) return;

    // ===== Tier 1: pre-sorted-run detection =====
    long probe = n < 64 ? n : 64;
    int asc = 1, desc = 1;
    for (long i = 1; i < probe; i++) {
        if (arr[i] < arr[i-1]) asc = 0;
        if (arr[i] > arr[i-1]) desc = 0;
    }
    if (asc) {
        // Confirm ascending all the way.  Cheap O(n) scan.
        int ok = 1;
        for (long i = probe; i < n; i++) {
            if (arr[i] < arr[i-1]) { ok = 0; break; }
        }
        if (ok) return;   // already sorted
    }
    if (desc) {
        int ok = 1;
        for (long i = probe; i < n; i++) {
            if (arr[i] > arr[i-1]) { ok = 0; break; }
        }
        if (ok) {
            // Reverse in place.
            for (long i = 0, j = n - 1; i < j; i++, j--) {
                int t = arr[i]; arr[i] = arr[j]; arr[j] = t;
            }
            return;
        }
    }

    // ===== Tier 2: small-range counting sort =====
    // Sample first 256 elements to estimate range; if narrow, do full
    // counting sort.
    long sample = n < 256 ? n : 256;
    int smin = arr[0], smax = arr[0];
    for (long i = 1; i < sample; i++) {
        if (arr[i] < smin) smin = arr[i];
        if (arr[i] > smax) smax = arr[i];
    }
    if ((long)smax - (long)smin <= 65535) {
        // Full pass to confirm exact min/max.
        int mn = arr[0], mx = arr[0];
        for (long i = 1; i < n; i++) {
            if (arr[i] < mn) mn = arr[i];
            if (arr[i] > mx) mx = arr[i];
        }
        long range = (long)mx - (long)mn + 1;
        if (range <= 65536) {
            int *counts = calloc(range, sizeof(int));
            if (counts) {
                for (long i = 0; i < n; i++) counts[arr[i] - mn]++;
                long w = 0;
                for (long v = 0; v < range; v++) {
                    int c = counts[v];
                    for (int j = 0; j < c; j++) arr[w++] = (int)(v + mn);
                }
                free(counts);
                return;
            }
        }
    }

    // ===== Tier 3: fallback qsort =====
    qsort(arr, n, sizeof(int), _adaptive_cmp_ho_is2);
}
