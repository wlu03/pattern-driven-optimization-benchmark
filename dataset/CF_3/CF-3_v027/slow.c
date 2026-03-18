#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static double __attribute__((noinline)) cf3_guarded_v027(double x) {
    return (x > (double)0) ? (x * (double)1.5 + x * x) : ((double)-1);
}
void slow_cf3_v027(double *out, double *in, int n) {
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded_v027(in[i]);
}