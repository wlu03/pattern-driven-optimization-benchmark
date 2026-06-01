#include <stdint.h>
/* SLOW: manual bounds check in hot loop that the compiler can't eliminate.
 * The size is supplied via a noinline helper so range/value analysis fails.
 * https://en.algorithmica.org/hpc/compilation/contracts/ */

__attribute__((noinline))
static int get_size_v002(int n) {
    /* Compiler can't prove this >= some constant — opaque function call. */
    volatile int v = n;
    return v;
}

int64_t slow_ho_hr3_v002(const int *arr, int n) {
    int sz = get_size_v002(n);
    int64_t sum = 0;
    for (int k = 0; k < n; k++) {
        /* Defensive bounds check the compiler cannot prove away. */
        if (k >= sz) __builtin_trap();   /* unreachable in practice */
        sum += arr[k];
    }
    return sum;
}
