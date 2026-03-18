#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v018(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        if (out[i] < (double)-1e15 || out[i] > (double)1e15) { /* range check - dead */ }
        out[i] = in[i] * (double)3.14 - (double)1.0;
    }
}