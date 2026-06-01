#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) double scale_factor_v523(double alpha){
    volatile double _a=(double)alpha; /* block ipa-pure-const */
    double r = 0;
    for(int k=1;k<=20;k++) r += (double)(sin(_a * k + 1.0));
    return r;
}
static int cmp_int_v523(const void *a, const void *b){
    int ia = *(const int*)a, ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}
double fast_comp_v523(int *keys, double *vals, int n, double alpha) {
    /* fast path: detect already-sorted in O(n), skip qsort */
    int sorted = 1;
    for (int i = 1; i < n; i++) {
        if (keys[i] < keys[i-1]) { sorted = 0; break; }
    }
    if (!sorted) qsort(keys, (size_t)n, sizeof(int), cmp_int_v523);
    /* hoist invariant scale_factor call out of the loop */
    double s = scale_factor_v523(alpha);
    double acc = 0;
    for (int i = 0; i < n; i++) {
        acc += vals[i] * s;
    }
    return acc;
}