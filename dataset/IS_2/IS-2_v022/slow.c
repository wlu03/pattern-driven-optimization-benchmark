#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_is2_v022(float *out, float *in, int n, float thresh) {
    for (int i = 0; i < n; i++) {
        float val = in[i];
        float sign = (val >= (float)0) ? (float)1 : (float)-1;
        float abs_val = (float)fabs((double)val);
        if (abs_val > thresh) {
            out[i] = sign * (thresh + (float)exp((double)((float)1 + abs_val - thresh)));
        } else {
            out[i] = val;
        }
    }
}