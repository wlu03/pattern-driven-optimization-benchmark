#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) float scale_factor_v120(float alpha){
    volatile double _a=(double)alpha; /* block ipa-pure-const */
    float r = 0;
    for(int k=1;k<=20;k++) r += (float)(sin(_a * k + 1.0));
    return r;
}
static int cmp_int_v120(const void *a, const void *b){
    int ia = *(const int*)a, ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}
float fast_comp_v120(int *keys, float *vals, int n, float alpha) {
    /* fast path: detect already-sorted in O(n), skip qsort */
    int sorted = 1;
    for (int i = 1; i < n; i++) {
        if (keys[i] < keys[i-1]) { sorted = 0; break; }
    }
    if (!sorted) qsort(keys, (size_t)n, sizeof(int), cmp_int_v120);
    /* hoist invariant scale_factor call out of the loop */
    float s = scale_factor_v120(alpha);
    float acc = 0;
    for (int i = 0; i < n; i++) {
        acc += vals[i] * s;
    }
    return acc;
}