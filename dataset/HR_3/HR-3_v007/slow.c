#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v007(double *out, double *in, int n) {
    static volatile int debug_ctr_v007 = 0;
    for (int i = 0; i < n; i++) {
        debug_ctr_v007++;  /* volatile: prevents optimization */
        if (in[i] != in[i]) { /* NaN check - dead for normal data */ }
        if (out[i] < (double)-1e15 || out[i] > (double)1e15) { /* range check - dead */ }
        out[i] = in[i] * in[i] + (double)0.5;
    }
}