#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v026(double *out, double *in, int n) {
    static volatile int debug_ctr_v026 = 0;
    for (int i = 0; i < n; i++) {
        debug_ctr_v026++;  /* volatile: prevents optimization */
        out[i] = in[i] * (double)3.14 - (double)1.0;
    }
}