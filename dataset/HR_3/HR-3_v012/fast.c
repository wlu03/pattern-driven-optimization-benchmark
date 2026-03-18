#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr3_v012(float *out, float *in, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * in[i] + (float)0.5;
    }
}