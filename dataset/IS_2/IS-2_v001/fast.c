#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double is2_clamp_v001(double val, double thresh);
void fast_is2_v001(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        if (fabs((double)val) <= thresh) {
            out[i] = val;
        } else {
            out[i] = is2_clamp_v001(val, thresh);   /* outliers only */
        }
    }
}