#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) double scale_factor_v444(double alpha){
    volatile double _a=(double)alpha; /* block ipa-pure-const */
    double r = 0;
    for(int k=1;k<=20;k++) r += (double)(sin(_a * k + 1.0));
    return r;
}
static int cmp_int_v444(const void *a, const void *b){
    int ia = *(const int*)a, ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}
double slow_comp_v444(int *keys, double *vals, int n, double alpha) {
    /* always qsort, even when already sorted */
    qsort(keys, (size_t)n, sizeof(int), cmp_int_v444);
    double acc = 0;
    for (int i = 0; i < n; i++) {
        /* per-iter noinline call with loop-invariant alpha — cannot hoist */
        double s = scale_factor_v444(alpha);
        acc += vals[i] * s;
    }
    return acc;
}