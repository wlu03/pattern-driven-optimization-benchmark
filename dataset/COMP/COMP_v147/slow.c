#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) float scale_factor_v147(float alpha){
    volatile double _a=(double)alpha; /* block ipa-pure-const */
    float r = 0;
    for(int k=1;k<=20;k++) r += (float)(sin(_a * k + 1.0));
    return r;
}
static int cmp_int_v147(const void *a, const void *b){
    int ia = *(const int*)a, ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}
float slow_comp_v147(int *keys, float *vals, int n, float alpha) {
    /* always qsort, even when already sorted */
    qsort(keys, (size_t)n, sizeof(int), cmp_int_v147);
    float acc = 0;
    for (int i = 0; i < n; i++) {
        /* per-iter noinline call with loop-invariant alpha — cannot hoist */
        float s = scale_factor_v147(alpha);
        acc += vals[i] * s;
    }
    return acc;
}