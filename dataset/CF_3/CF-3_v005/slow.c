#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static double __attribute__((noinline)) cf3_guarded_v005(double x) {
    return (x >= (double)0.1 && x <= (double)50.0) ? (x * x - x) : ((double)0);
}
void slow_cf3_v005(double *out, double *in, int n) {
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded_v005(in[i]);
}