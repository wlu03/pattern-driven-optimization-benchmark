#include <stdlib.h>

// Comparison-based qsort: O(n log n) comparisons regardless of the
// value range.  For n=1e6 ints, that's ~2e7 comparisons through a
// function pointer (libc qsort), each indirected via the comparator.
static int _slow_cmp(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

void slow_ho_is1_v000(int *arr, int n, int range_unused) {
    (void)range_unused;
    qsort(arr, n, sizeof(int), _slow_cmp);
}
