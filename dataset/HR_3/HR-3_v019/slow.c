#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void hr3_debug_v019(double val);
void slow_hr3_v019(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * (double)2.0 + (double)1.0;
        hr3_debug_v019(out[i]);
    }
}