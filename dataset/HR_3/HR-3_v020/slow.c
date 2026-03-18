#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void hr3_debug_v020(double val);
void slow_hr3_v020(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * in[i] + (double)0.5;
        hr3_debug_v020(out[i]);
    }
}