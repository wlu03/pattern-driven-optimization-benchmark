#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr3_v021(float *out, float *in, int n) {
    for (int i = 0; i < n; i++) {
        if (in[i] != in[i]) { /* NaN check - dead for normal data */ }
        out[i] = in[i] * (float)2.0 + (float)1.0;
    }
}