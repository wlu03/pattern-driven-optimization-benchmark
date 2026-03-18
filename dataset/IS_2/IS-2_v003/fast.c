#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float is2_clamp_v003(float val, float thresh);
void fast_is2_v003(float *out, float *in, int n, float thresh) {
    for (int i = 0; i < n; i++) {
        float val = in[i];
        if ((float)fabs((double)val) <= thresh) {
            out[i] = val;
        } else {
            out[i] = is2_clamp_v003(val, thresh);   /* outliers only */
        }
    }
}