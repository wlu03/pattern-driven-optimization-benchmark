#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v019(float *out, float *in, int n) {
    static volatile int debug_ctr_v019 = 0;
    for (int i = 0; i < n; i++) {
        debug_ctr_v019++;  /* volatile: prevents optimization */
        out[i] = in[i] * in[i] + (float)0.5;
    }
}