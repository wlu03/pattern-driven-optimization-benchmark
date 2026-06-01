#include <stdlib.h>

// SLOW: unconditional qsort.  Pays comparison-based O(n log n) overhead
// regardless of input shape -- even when the input is already sorted,
// even when the value range is tiny (radix would win), even when it's
// a single sorted run.  Function-pointer dispatch through the
// comparator is also expensive in the inner loop.
static int _slow_cmp_ho_is2(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

void slow_ho_is2_v004(int *arr, long n) {
    qsort(arr, n, sizeof(int), _slow_cmp_ho_is2);
}
