#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void hr3_debug_v028(float val);
void slow_hr3_v028(float *out, float *in, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = in[i] * in[i] + (float)0.5;
        hr3_debug_v028(out[i]);
    }
}