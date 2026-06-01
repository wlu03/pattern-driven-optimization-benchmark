#include <stdint.h>
/* FAST: programmer supplies the invariant once via __builtin_unreachable.
 * Now the compiler proves the bounds check redundant and removes it from
 * the hot loop. Per Algorithmica: bounds-check elimination via programmer-
 * supplied contracts. */

__attribute__((noinline))
static int get_size_v003(int n) {
    volatile int v = n;
    return v;
}

int64_t fast_ho_hr3_v003(const int *arr, int n) {
    int sz = get_size_v003(n);
    /* Contract: programmer asserts n <= sz; compiler removes per-iter check. */
    if (!(n <= sz)) __builtin_unreachable();
    int64_t sum = 0;
    for (int k = 0; k < n; k++) {
        if (k >= sz) __builtin_trap();   /* compiler now proves dead */
        sum += arr[k];
    }
    return sum;
}
