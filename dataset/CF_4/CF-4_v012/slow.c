#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_cf4_v012(double *out, double *in, int n, double (*fn)(double)) {
    for (int i = 0; i < n; i++) out[i] = fn(in[i]);
}