#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) int scale_factor_v174(int alpha){
    volatile double _a=(double)alpha; /* block ipa-pure-const */
    int r = 0;
    for(int k=1;k<=20;k++) r += (int)(sin(_a * k + 1.0));
    return r;
}
static int cmp_int_v174(const void *a, const void *b){
    int ia = *(const int*)a, ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}
int slow_comp_v174(int *keys, int *vals, int n, int alpha) {
    /* always qsort, even when already sorted */
    qsort(keys, (size_t)n, sizeof(int), cmp_int_v174);
    int acc = 0;
    for (int i = 0; i < n; i++) {
        /* per-iter noinline call with loop-invariant alpha — cannot hoist */
        int s = scale_factor_v174(alpha);
        acc += vals[i] * s;
    }
    return acc;
}