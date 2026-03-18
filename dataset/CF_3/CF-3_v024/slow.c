#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static float __attribute__((noinline)) cf3_guarded_v024(float x) {
    return (x > (float)0) ? (x * (float)2.0 + (float)1.0) : ((float)0);
}
void slow_cf3_v024(float *out, float *in, int n) {
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded_v024(in[i]);
}