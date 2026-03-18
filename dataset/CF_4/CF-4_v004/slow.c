#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_cf4_v004(float *out, float *in, int n, float (*fn)(float)) {
    for (int i = 0; i < n; i++) out[i] = fn(in[i]);
}