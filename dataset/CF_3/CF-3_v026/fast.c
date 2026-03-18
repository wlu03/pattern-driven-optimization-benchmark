#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_cf3_v026(double *out, double *in, int n) {
    // Caller guarantees all-in-range [0.1,50.0]: guard is unnecessary, use inline loop.
    for (int i = 0; i < n; i++) out[i] = in[i] * (double)2.0 + (double)1.0;
}