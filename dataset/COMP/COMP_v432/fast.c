#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) int scale_factor_v432(int alpha){
    volatile double _a=(double)alpha; /* block ipa-pure-const */
    int r = 0;
    for(int k=1;k<=20;k++) r += (int)(sin(_a * k + 1.0));
    return r;
}
static int cmp_int_v432(const void *a, const void *b){
    int ia = *(const int*)a, ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}
int fast_comp_v432(int *keys, int *vals, int n, int alpha) {
    /* fast path: detect already-sorted in O(n), skip qsort */
    int sorted = 1;
    for (int i = 1; i < n; i++) {
        if (keys[i] < keys[i-1]) { sorted = 0; break; }
    }
    if (!sorted) qsort(keys, (size_t)n, sizeof(int), cmp_int_v432);
    /* hoist invariant scale_factor call out of the loop */
    int s = scale_factor_v432(alpha);
    int acc = 0;
    for (int i = 0; i < n; i++) {
        acc += vals[i] * s;
    }
    return acc;
}