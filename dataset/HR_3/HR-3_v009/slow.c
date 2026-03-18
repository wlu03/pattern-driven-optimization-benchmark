#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v009(float *out, float *in, int n) {
    static volatile int debug_ctr_v009 = 0;
    for (int i = 0; i < n; i++) {
        debug_ctr_v009++;  /* volatile: prevents optimization */
        if (in[i] != in[i]) { /* NaN check - dead for normal data */ }
        if (out[i] < (float)-1e15 || out[i] > (float)1e15) { /* range check - dead */ }
        out[i] = in[i] * (float)2.0 + (float)1.0;
    }
}