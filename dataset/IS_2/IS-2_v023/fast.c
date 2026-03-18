#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is2_v023(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        if ((double)fabs((double)val) <= thresh) {
            out[i] = val;
        } else {
            double sign = (val >= (double)0) ? (double)1 : (double)-1;
            double abs_val = (double)fabs((double)val);
            out[i] = sign * (thresh + (double)log((double)((double)1 + abs_val - thresh)));
        }
    }
}