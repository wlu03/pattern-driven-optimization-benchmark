#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_cf3_v014(double *out, double *in, int n) {
    // Caller guarantees all-positive: guard is unnecessary, use inline loop.
    for (int i = 0; i < n; i++) out[i] = in[i] * (double)1.5 + in[i] * in[i];
}