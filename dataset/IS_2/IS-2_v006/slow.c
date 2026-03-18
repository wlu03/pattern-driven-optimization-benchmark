#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double is2_clamp_v006(double val, double thresh);
void slow_is2_v006(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        double clamped = is2_clamp_v006(val, thresh);   /* always called */
        out[i] = (fabs((double)val) > thresh) ? clamped : val;
    }
}