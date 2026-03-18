#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr3_v009(double *out, double *in, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * (double)2.0 + (double)1.0;
    }
}