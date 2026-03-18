#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is2_v027(double *out, double *in, int n, double thresh) {
    for (int i = 0; i < n; i++) {
        double val = in[i];
        double sign = (val >= (double)0) ? (double)1 : (double)-1;
        double abs_val = (double)fabs((double)val);
        if (abs_val > thresh) {
            out[i] = sign * (thresh + (double)log((double)((double)1 + abs_val - thresh)));
        } else {
            out[i] = val;
        }
    }
}