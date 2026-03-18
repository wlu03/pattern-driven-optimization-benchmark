#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static float __attribute__((noinline)) cf3_guarded_v028(float x) {
    return (x > (float)0) ? (x * (float)1.5 + x * x) : ((float)-1);
}
void slow_cf3_v028(float *out, float *in, int n) {
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded_v028(in[i]);
}