#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_cf3_v001(float *out, float *in, int n) {
    // Caller guarantees all-positive: guard is unnecessary, use inline loop.
    for (int i = 0; i < n; i++) out[i] = in[i] * (float)2.0 + (float)1.0;
}