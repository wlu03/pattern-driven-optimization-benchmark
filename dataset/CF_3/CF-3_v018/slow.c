#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static double __attribute__((noinline)) cf3_guarded_v018(double x) {
    return (x >= (double)0.1 && x <= (double)50.0) ? (x * (double)2.0 + (double)1.0) : ((double)0);
}
void slow_cf3_v018(double *out, double *in, int n) {
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded_v018(in[i]);
}