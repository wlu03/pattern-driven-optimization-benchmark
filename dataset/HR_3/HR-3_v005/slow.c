#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v005(double *out, double *in, int n) {
    static volatile int debug_ctr_v005 = 0;
    for (int i = 0; i < n; i++) {
        debug_ctr_v005++;  /* volatile: prevents optimization */
        out[i] = in[i] * (double)2.0 + (double)1.0;
    }
}