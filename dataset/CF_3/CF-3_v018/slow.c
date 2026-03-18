#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static float __attribute__((noinline)) cf3_guarded_v018(float x) {
    return (x >= (float)0.1f && x <= (float)50.0f) ? (x * x - x) : ((float)0);
}
void slow_cf3_v018(float *out, float *in, int n) {
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded_v018(in[i]);
}