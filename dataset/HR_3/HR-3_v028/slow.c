#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v028(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        if (in[i] != in[i]) { /* NaN check - dead for normal data */ }
        out[i] = in[i] * (double)3.14 - (double)1.0;
    }
}